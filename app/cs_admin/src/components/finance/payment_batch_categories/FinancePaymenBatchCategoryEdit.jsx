// @flow

import React from 'react'
import gql from "graphql-tag"
import { useQuery, useMutation } from "react-apollo";
import { withTranslation } from 'react-i18next'
import { withRouter } from "react-router"
import { Formik } from 'formik'
import { toast } from 'react-toastify'

import { GET_PAYMENT_BATCH_CATEGORIES_QUERY, GET_PAYMENT_BATCH_CATEGORY_QUERY } from './queries'
// import { PAYMENT_METHOD_SCHEMA } from './yupSchema'



import {
  Card,
} from "tabler-react";
import HasPermissionWrapper from "../../HasPermissionWrapper"

import FinancePaymentBatchCategoriesBase from './FinancePaymentBatchCategoriesBase'
import FinancePaymentBatchCategoriesForm from './FinancePaymentBatchCategoriesForm'


const UPDATE_PAYMENT_BATCH_CATEGORY = gql`
  mutation UpdateFinancePaymentBatchCategory($input: UpdateFinancePaymentBatchCategoryInput!) {
    updateFinancePaymentMethod(input: $input) {
      financePaymentMethod {
        id
        name
        code
      }
    }
  }
`

function FinancePaymentBatchCategoryEdit({ t, history, match }) {
  const returnUrl = "/finance/paymentbatchcategories"
  const paymentBatchCategoryId = match.params.id

  const { loading, error, data } = useQuery(GET_PAYMENT_BATCH_CATEGORY_QUERY, {
    variables: {'id': paymentBatchCategoryId},
  })
  const [updateFinancePaymentBatchCategory] = useMutation(UPDATE_PAYMENT_BATCH_CATEGORY)

  // Loading
  if (loading) return (
    <FinancePaymentBatchCategoriesBase>
      <ContentCard cardTitle={t('finance.payment_batch_categories.title')}>
        <Dimmer active={true}
                loader={true}>
        </Dimmer>
      </ContentCard>
    </FinancePaymentBatchCategoriesBase>
  )
  // Error
  if (error) return (
    <FinancePaymentBatchCategoriesBase>
      <ContentCard cardTitle={t('finance.payment_batch_categories.title')}>
        <p>{t('finance.payment_batch_categories.error_loading')}</p>
      </ContentCard>
      </FinancePaymentBatchCategoriesBase>
  )

  initialData = data.financePaymentBatchCategory

  return (
    <FinancePaymentBatchCategoriesBase>
      <Card>
        <Card.Header>
          <Card.Title>{t('finance.payment_methods.title_add')}</Card.Title>
        </Card.Header>
          <Formik
            initialValues={{ 
              name: initialData.name, 
              batchCategoryType: initialData.batchCategoryType,
              description: initialData.description,
            }}
            // validationSchema={PAYMENT_METHOD_SCHEMA}
            onSubmit={(values, { setSubmitting }) => {
              console.log('submit values:')
              console.log(values)

              updateFinancePaymentBatchCategory({ variables: {
                input: {
                  id: match.params.id,
                  name: values.name, 
                  batchCategoryType: values.batchCategoryType,
                  description: values.description
                }
              }, refetchQueries: [
                {query: GET_PAYMENT_BATCH_CATEGORIES_QUERY, variables: get_list_query_variables()}
              ]})
              .then(({ data }) => {
                  console.log('got data', data)
                  toast.success((t('finance.payment_batch_categories.toast_edit_success')), {
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
            {({ isSubmitting, errors, values }) => (
                <FinancePaymentBatchCategoriesForm
                  isSubmitting={isSubmitting}
                  errors={errors}
                  values={values}
                  returnUrl={returnUrl}
                />
               
            )}
          </Formik>
      </Card>
    </FinancePaymentBatchCategoriesBase>
  )
}

export default withTranslation()(withRouter(FinancePaymentBatchCategoryEdit))