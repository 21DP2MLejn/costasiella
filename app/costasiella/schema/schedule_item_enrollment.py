from django.utils.translation import gettext as _

import datetime
import pytz
import graphene
from django.utils import timezone
from django.conf import settings
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError

from ..models import Account, AccountSubscription, ScheduleItem, ScheduleItemEnrollment
from ..modules.gql_tools import require_login, require_login_and_permission, \
                                require_login_and_one_of_permissions, get_rid
from ..modules.messages import Messages

from ..dudes import ClassCheckinDude, ClassScheduleDude

m = Messages()


class ScheduleItemEnrollmentNode(DjangoObjectType):
    class Meta:
        model = ScheduleItemEnrollment
        # account_schedule_event_ticket_Isnull filter can be used to differentiate class & event enrollment
        filter_fields = {
            'schedule_item': ['exact'],
            'account': ['exact'],
            'account_subscription': ['exact'],
            'date_start': ['exact', 'gte', 'lte'],
            'date_end': ['exact', 'gte', 'lte', 'isnull']
        }
        interfaces = (graphene.relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        user = info.context.user
        require_login_and_permission(user, 'costasiella.view_scheduleitemenrollment')

        return cls._meta.model.objects.get(id=id)


class ScheduleItemEnrollmentQuery(graphene.ObjectType):
    schedule_item_enrollments = DjangoFilterConnectionField(ScheduleItemEnrollmentNode)
    schedule_item_enrollment = graphene.relay.Node.Field(ScheduleItemEnrollmentNode)

    def resolve_schedule_item_enrollments(self, info, **kwargs):
        user = info.context.user
        require_login(user)

        view_permission = user.has_perm('costasiella.view_scheduleitemenrollment')

        if view_permission and 'account' in kwargs:
            # Allow user to filter by any account
            rid = get_rid(kwargs.get('account', user.id))
            account_id = rid.id
        elif view_permission:
            # return all
            account_id = None
        else:
            # A user can only query their own orders
            account_id = user.id

        if account_id:
            order_by = '-date_start'
            return ScheduleItemEnrollment.objects.filter(account=account_id).order_by(order_by)
        else:
            order_by = '-account__full_name'
            return ScheduleItemEnrollment.objects.all().order_by(order_by)
            

def validate_schedule_item_enrollment_create_update_input(input):
    """
    Validate input
    """ 
    result = {}

    # Check Account
    if 'account' in input:
        if input['account']:
            rid = get_rid(input['account'])
            account = Account.objects.filter(id=rid.id).first()
            result['account'] = account
            if not account:
                raise Exception(_('Invalid Account ID!'))

    # Check AccountSubscription
    if 'account_subscription' in input:
        if input['account_subscription']:
            rid = get_rid(input['account_subscription'])
            account_subscription = AccountSubscription.objects.filter(id=rid.id).first()
            result['account_subscription'] = account_subscription
            if not account_subscription:
                raise Exception(_('Invalid Account Subscription ID!'))

    # Check Schedule Item
    if 'schedule_item' in input:
        if input['schedule_item']:
            rid = get_rid(input['schedule_item'])
            schedule_item = ScheduleItem.objects.get(id=rid.id)
            result['schedule_item'] = schedule_item
            if not schedule_item:
                raise Exception(_('Invalid Schedule Item (class) ID!'))        

    return result


class CreateScheduleItemEnrollment(graphene.relay.ClientIDMutation):
    class Input:
        account = graphene.ID(required=False)
        schedule_item = graphene.ID(required=True)
        account_classpass = graphene.ID(required=False)
        account_subscription = graphene.ID(required=False)
        organization_classpass = graphene.ID(required=False)
        finance_invoice_item = graphene.ID(required=False)
        enrollment_type = graphene.String(required=True)
        date = graphene.types.datetime.Date(required=True)
        online_booking = graphene.Boolean(required=False, default_value=False)
        booking_status = graphene.String(required=False, default_value="BOOKED")

    schedule_item_enrollment = graphene.Field(ScheduleItemEnrollmentNode)

    @classmethod
    def mutate_and_get_payload(self, root, info, **input):
        user = info.context.user
        require_login(user)

        permission = user.has_perm('costasiella.add_scheduleitemenrollment') or \
            user.has_perm('costasiella.view_selfcheckin')

        validation_result = validate_schedule_item_enrollment_create_update_input(input)
        if not permission or 'account' not in input:
            # When the user doesn't have permissions; always use their own account
            validation_result['account'] = user

        class_checkin_dude = ClassCheckinDude()
        class_schedule_dude = ClassScheduleDude()

        class_takes_place = class_schedule_dude.schedule_item_takes_place_on_day(
            schedule_item=validation_result['schedule_item'],
            date=input['date']
        )
        
        if not class_takes_place:
            raise Exception(
                _("This class doesn't take place on this date, please check for the correct date or any holidays.")
            )

        enrollment_type = input['enrollment_type']
        if enrollment_type == "CLASSPASS":
            if not validation_result['account_classpass']:
                raise Exception(_('accountClasspass field is mandatory when doing a class pass check-in'))

            account_classpass = validation_result['account_classpass']
            schedule_item_enrollment = class_checkin_dude.class_checkin_classpass(
                account=validation_result['account'],
                account_classpass=account_classpass,
                schedule_item=validation_result['schedule_item'],
                date=input['date'],
                booking_status=input['booking_status'],
                online_booking=input['online_booking'],
            )

            account_classpass.update_classes_remaining()

        elif enrollment_type == "SUBSCRIPTION":
            if not validation_result['account_subscription']:
                raise Exception(_('accountSubscription field is mandatory when doing a subscription check-in'))

            print("SUBSCRIPTION checkin")

            account_subscription = validation_result['account_subscription']
            schedule_item_enrollment = class_checkin_dude.class_checkin_subscription(
                account=validation_result['account'],
                account_subscription=account_subscription,
                schedule_item=validation_result['schedule_item'],
                date=input['date'],
                booking_status=input['booking_status'],
                online_booking=input['online_booking'],
            )

        elif enrollment_type == "CLASSPASS_BUY_AND_BOOK":
            if not validation_result['organization_classpass']:
                raise Exception(_('organizationClasspass field is mandatory when doing a classpass buy and check-in'))

            organization_classpass = validation_result['organization_classpass']
            result = class_checkin_dude.sell_classpass_and_class_checkin(
                account = validation_result['account'],
                organization_classpass = organization_classpass,
                schedule_item = validation_result['schedule_item'],
                date = input['date'],
                booking_status = input['booking_status'],
                online_booking = input['online_booking'],                    
            )

            schedule_item_enrollment = result['schedule_item_enrollment']
            account_classpass = result['account_classpass']

            account_classpass.update_classes_remaining()

        return CreateScheduleItemEnrollment(schedule_item_enrollment=schedule_item_enrollment)


class UpdateScheduleItemEnrollment(graphene.relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        booking_status = graphene.String(required=False, default_value="BOOKED")
        
    schedule_item_enrollment = graphene.Field(ScheduleItemEnrollmentNode)

    @classmethod
    def mutate_and_get_payload(self, root, info, **input):
        user = info.context.user
        require_login_and_one_of_permissions(user, [
            'costasiella.change_scheduleitemenrollment',
            'costasiella.view_selfcheckin'
        ])

        rid = get_rid(input['id'])
        schedule_item_enrollment = ScheduleItemEnrollment.objects.filter(id=rid.id).first()
        if not schedule_item_enrollment:
            raise Exception('Invalid Schedule Item Enrollment ID!')

        validation_result = validate_schedule_item_enrollment_create_update_input(input)
        
        if 'booking_status' in input:
            schedule_item_enrollment.booking_status = input['booking_status']

        schedule_item_enrollment.save()

        # Update classpass classes remaining
        if schedule_item_enrollment.account_classpass:
             schedule_item_enrollment.account_classpass.update_classes_remaining()

        # Refund subscription credit (remove it)
        if schedule_item_enrollment.account_subscription:
            if input['booking_status'] == 'CANCELLED':
                AccountSubscriptionCredit.objects.filter(
                    schedule_item_enrollment=schedule_item_enrollment,
                ).delete()
            if input['booking_status'] == 'BOOKED' or input['booking_status'] == 'ATTENDING':
                qs = AccountSubscriptionCredit.objects.filter(
                    schedule_item_enrollment=schedule_item_enrollment
                )
                if not qs.exists():
                    from ..dudes import ClassCheckinDude
                    class_checkin_dude = ClassCheckinDude()
                    class_checkin_dude.class_checkin_subscription_subtract_credit(schedule_item_enrollment)

        return UpdateScheduleItemEnrollment(schedule_item_enrollment=schedule_item_enrollment)


class DeleteScheduleItemEnrollment(graphene.relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(self, root, info, **input):
        user = info.context.user
        require_login_and_one_of_permissions(user, [
            'costasiella.delete_scheduleitemenrollment',
            'costasiella.view_selfcheckin'
        ])

        rid = get_rid(input['id'])
        schedule_item_enrollment = ScheduleItemEnrollment.objects.filter(id=rid.id).first()
        if not schedule_item_enrollment:
            raise Exception('Invalid Schedule Item Enrollment ID!')

        # Get linked class pass if any
        account_classpass = None
        if schedule_item_enrollment.account_classpass:
             account_classpass = schedule_item_enrollment.account_classpass

        # Actually remove
        ok = schedule_item_enrollment.delete()

        if account_classpass:
            account_classpass.update_classes_remaining()

        return DeleteScheduleItemEnrollment(ok=ok)


class ScheduleItemEnrollmentMutation(graphene.ObjectType):
    delete_schedule_item_enrollment = DeleteScheduleItemEnrollment.Field()
    create_schedule_item_enrollment = CreateScheduleItemEnrollment.Field()
    update_schedule_item_enrollment = UpdateScheduleItemEnrollment.Field()
