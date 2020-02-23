from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q, FilteredRelation, OuterRef, Subquery


import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from graphql_relay import to_global_id

from ..models import ScheduleItem, ScheduleItemWeeklyOTC, OrganizationClasstype, OrganizationLevel, OrganizationLocationRoom
from ..modules.gql_tools import require_login_and_permission, require_login_and_one_of_permissions, get_rid
from ..modules.messages import Messages
from ..modules.model_helpers.schedule_item_helper import ScheduleItemHelper
from .account import AccountNode
from .organization_classtype import OrganizationClasstypeNode
from .organization_level import OrganizationLevelNode
from .organization_location_room import OrganizationLocationRoomNode
from .schedule_item import ScheduleItemNode

from ..dudes.insight_account_classpasses_dude import InsightAccountClasspassesDude


m = Messages()

import datetime


class AccountClasspassesSoldType(graphene.ObjectType):
    description = graphene.String()
    data = graphene.List(graphene.Int)
    year = graphene.Int()

    def resolve_description(self, info):
        return _("account_classpasses_sold")

    def resolve_data(self, info):       
        insight_account_classpasses_dude = InsightAccountClasspassesDude()
        year = self.year
        if not year:
            year = timezone.now().year

        data = insight_account_classpasses_dude.get_classpasses_sold_year_summary_count(self.year)

        return data


class AccountClasspassesCurrentType(graphene.ObjectType):
    description = graphene.String()
    data = graphene.List(graphene.Int)
    year = graphene.Int()

    def resolve_description(self, info):
        return _("account_classpasses_current")

    def resolve_data(self, info):       
        insight_account_classpasses_dude = InsightAccountClasspassesDude()
        year = self.year
        if not year:
            year = timezone.now().year

        data = insight_account_classpasses_dude.get_classpasses_current_year_summary_count(self.year)

        return data


class InsightQuery(graphene.ObjectType):
    insight_account_classpasses_sold = graphene.Field(AccountClasspassesSoldType, year=graphene.Int())
    insight_account_classpasses_current = graphene.Field(AccountClasspassesCurrentType, year=graphene.Int())


    def resolve_insight_account_classpasses_sold(self, 
                                                 info, 
                                                 year=graphene.Int(required=True, default_value=timezone.now().year)):
        user = info.context.user
        require_login_and_permission(user, 'costasiella.view_insightclasspassessold')

        print('############ resolve')
        print(locals())

        account_classpasses_sold = AccountClasspassesSoldType()
        account_classpasses_sold.year = year

        return account_classpasses_sold


    def resolve_insight_account_classpasses_current(self, 
                                                    info, 
                                                    year=graphene.Int(required=True, default_value=timezone.now().year)):
        user = info.context.user
        require_login_and_permission(user, 'costasiella.view_insightclasspassescurrent')

        print('############ resolve')
        print(locals())

        account_classpasses_current = AccountClasspassesCurrentType()
        account_classpasses_current.year = year

        return account_classpasses_current
