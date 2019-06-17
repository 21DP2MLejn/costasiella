// @flow

import React, {Component } from 'react'
import gql from "graphql-tag"
import { Query, Mutation } from "react-apollo";
import { withTranslation } from 'react-i18next'
import { withRouter } from "react-router"
import { Link } from 'react-router-dom'

import { Formik } from 'formik'
import { toast } from 'react-toastify'

import { GET_ACCOUNT_SUBSCRIPTIONS_QUERY, GET_ACCOUNT_SUBSCRIPTION_QUERY } from './queries'
import { SUBSCRIPTION_SCHEMA } from './yupSchema'
import AccountSubscriptionForm from './AccountSubscriptionForm'

import {
  Page,
  Grid,
  Icon,
  Button,
  Card,
  Container,
} from "tabler-react";
import SiteWrapper from "../../../SiteWrapper"
import HasPermissionWrapper from "../../../HasPermissionWrapper"
import { dateToLocalISO } from '../../../../tools/date_tools'

import ProfileMenu from "../ProfileMenu"


const UPDATE_ACCOUNT_SUBSCRIPTION = gql`
  mutation UpdateAccountSubscription($input: UpdateAccountSubscriptionInput!) {
    updateAccountSubscription(input: $input) {
      accountSubscription {
        id
        account {
          id
          firstName
          lastName
          email
        }
        organizationSubscription {
          id
          name
        }
        financePaymentMethod {
          id
          name
        }
        dateStart
        dateEnd
        note
        registrationFeePaid        
      }
    }
  }
`


class AccountSubscriptionEdit extends Component {
  constructor(props) {
    super(props)
    console.log("Account subscription add props:")
    console.log(props)
  }

  render() {
    const t = this.props.t
    const history = this.props.history
    const match = this.props.match
    const id = match.params.id
    const account_id = match.params.account_id
    const return_url = "/relations/accounts/" + account_id + "/subscriptions"

    return (
      <SiteWrapper>
        <div className="my-3 my-md-5">
        <Query query={GET_ACCOUNT_SUBSCRIPTION_QUERY} variables = {{archived: false,  accountId: account_id, id: id}} >
          {({ loading, error, data, refetch }) => {
            // Loading
            if (loading) return <p>{t('general.loading_with_dots')}</p>
            // Error
            if (error) {
              console.log(error)
              return <p>{t('general.error_sad_smiley')}</p>
            }
            
            console.log('query data')
            console.log(data)
            const inputData = data
            const account = data.account
            const initialdata = data.accountSubscription

            let initialPaymentMethod = ""
            if (initialdata.financePaymentMethod) {
              initialPaymentMethod = initialdata.financePaymentMethod.id
            }

            return (
              <Container>
               <Page.Header title={account.firstName + " " + account.lastName} />
               <Grid.Row>
                  <Grid.Col md={9}>
                  <Card>
                    <Card.Header>
                      <Card.Title>{t('relations.account.subscriptions_title_edit')}</Card.Title>
                    </Card.Header>
                      <Mutation mutation={UPDATE_ACCOUNT_SUBSCRIPTION} onCompleted={() => history.push(return_url)}> 
                      {(createSubscription, { data }) => (
                          <Formik
                              initialValues={{ 
                                organizationSubscription: initialdata.organizationSubscription.id,
                                financePaymentMethod: initialPaymentMethod,
                                dateStart: initialdata.dateStart,
                                dateEnd: initialdata.dateEnd,
                                note: initialdata.note,
                                registrationFeePaid: initialdata.registrationFeePaid
                              }}
                              validationSchema={SUBSCRIPTION_SCHEMA}
                              onSubmit={(values, { setSubmitting }, errors) => {
                                  console.log('submit values:')
                                  console.log(values)
                                  console.log(errors)

                                  
                                  let dateEnd
                                  if (values.dateEnd) {
                                    dateEnd = dateToLocalISO(values.dateEnd)
                                  } else {
                                    dateEnd = values.dateEnd
                                  }

                                  createSubscription({ variables: {
                                    input: {
                                      id: id,
                                      account: account_id, 
                                      organizationSubscription: values.organizationSubscription,
                                      financePaymentMethod: values.financePaymentMethod,
                                      dateStart: dateToLocalISO(values.dateStart),
                                      dateEnd: dateEnd,
                                      note: values.note,
                                      registrationFeePaid: values.registrationFeePaid
                                    }
                                  }, refetchQueries: [
                                      // {query: GET_SUBSCRIPTIONS_QUERY, variables: {archived: false, accountId: account_id}}
                                  ]})
                                  .then(({ data }) => {
                                      console.log('got data', data)
                                      toast.success((t('relations.account.subscriptions_toast_edit_success')), {
                                          position: toast.POSITION.BOTTOM_RIGHT
                                        })
                                    }).catch((error) => {
                                      toast.error((t('general.toast_server_error')) + ': ' +  error, {
                                          position: toast.POSITION.BOTTOM_RIGHT
                                        })
                                      console.log('there was an error sending the query', error)
                                      setSubmitting(false)
                                    })
                              }}
                              >
                              {({ isSubmitting, setFieldValue, setFieldTouched, errors, values }) => (
                                <AccountSubscriptionForm
                                  inputData={inputData}
                                  isSubmitting={isSubmitting}
                                  setFieldValue={setFieldValue}
                                  setFieldTouched={setFieldTouched}
                                  errors={errors}
                                  values={values}
                                  return_url={return_url}
                                >
                                  {console.log(errors)}
                                </AccountSubscriptionForm>
                              )}
                          </Formik>
                      )}
                      </Mutation>
                    </Card>
                  </Grid.Col>
                  <Grid.Col md={3}>
                    <HasPermissionWrapper permission="change"
                                          resource="accountsubscription">
                      <Link to={return_url}>
                        <Button color="primary btn-block mb-6">
                          <Icon prefix="fe" name="chevrons-left" /> {t('general.back')}
                        </Button>
                      </Link>
                    </HasPermissionWrapper>
                    <ProfileMenu active_link='subscriptions'/>
                  </Grid.Col>
                </Grid.Row>
              </Container>
            )}}
          </Query>
        </div>
    </SiteWrapper>
    )}
  }


export default withTranslation()(withRouter(AccountSubscriptionEdit))
