from django.utils.translation import gettext as _
from django.utils import timezone

import graphene

from ..modules.gql_tools import require_login_and_permission
from ..modules.messages import Messages

from ..dudes import InsightAccountClasspassesDude

m = Messages()


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


class AccountClasspassesActiveType(graphene.ObjectType):
    description = graphene.String()
    data = graphene.List(graphene.Int)
    year = graphene.Int()

    def resolve_description(self, info):
        return _("account_classpasses_active")

    def resolve_data(self, info):       
        insight_account_classpasses_dude = InsightAccountClasspassesDude()
        year = self.year
        if not year:
            year = timezone.now().year

        data = insight_account_classpasses_dude.get_classpasses_active_year_summary_count(self.year)

        return data


class InsightClasspassesQuery(graphene.ObjectType):
    insight_account_classpasses_sold = graphene.Field(AccountClasspassesSoldType, year=graphene.Int())
    insight_account_classpasses_active = graphene.Field(AccountClasspassesActiveType, year=graphene.Int())

    def resolve_insight_account_classpasses_sold(self, 
                                                 info, 
                                                 year=graphene.Int(required=True, default_value=timezone.now().year)):
        user = info.context.user
        require_login_and_permission(user, 'costasiella.view_insightclasspasses')

        account_classpasses_sold = AccountClasspassesSoldType()
        account_classpasses_sold.year = year

        return account_classpasses_sold

    def resolve_insight_account_classpasses_active(self, 
                                                    info, 
                                                    year=graphene.Int(required=True, default_value=timezone.now().year)):
        user = info.context.user
        require_login_and_permission(user, 'costasiella.view_insightclasspasses')

        account_classpasses_active = AccountClasspassesActiveType()
        account_classpasses_active.year = year

        return account_classpasses_active

