from django.utils.translation import gettext as _
from django.utils import timezone
import graphene

from ..dudes import InsightRevenueDude
from ..modules.gql_tools import require_login_and_permission
from ..modules.finance_tools import display_float_as_amount


class InsightRevenueEventTicketsMonthType(graphene.ObjectType):
    month = graphene.Int()
    total = graphene.Decimal()
    total_display = graphene.String()
    subtotal = graphene.Decimal()
    tax = graphene.Decimal()


class InsightRevenueEventTicketsYearType(graphene.ObjectType):
    year = graphene.Int()
    months = graphene.List(InsightRevenueEventTicketsMonthType)

    def resolve_months(self, info):
        insight_revenue_dude = InsightRevenueDude()

        unprocessed_data = insight_revenue_dude.get_data_in_category(self.year, 'CLASSPASSES')

        months = []
        for item in unprocessed_data:
            insight_revenue_event_tickets_month_type = InsightRevenueEventTicketsMonthType()
            insight_revenue_event_tickets_month_type.month = item['month']
            insight_revenue_event_tickets_month_type.total = item['total']
            insight_revenue_event_tickets_month_type.total_display = display_float_as_amount(item['total'])
            insight_revenue_event_tickets_month_type.subtotal = item['subtotal']
            insight_revenue_event_tickets_month_type.tax = item['tax']

            months.append(insight_revenue_event_tickets_month_type)

        return months


class InsightRevenueEventTicketsQuery(graphene.ObjectType):
    insight_revenue_event_tickets = graphene.Field(InsightRevenueEventTicketsYearType, year=graphene.Int())

    def resolve_insight_revenue_event_tickets(self,
                                              info,
                                              year=graphene.Int(required=True, default_value=timezone.now().year)):
        user = info.context.user
        require_login_and_permission(user, 'costasiella.view_insightrevenue')

        revenue_event_tickets_year = InsightRevenueEventTicketsYearType()
        revenue_event_tickets_year.year = year

        return revenue_event_tickets_year
