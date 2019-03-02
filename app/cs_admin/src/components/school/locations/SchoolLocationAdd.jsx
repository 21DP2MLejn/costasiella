import React from 'react'
import { Mutation } from "react-apollo";
import gql from "graphql-tag"
import { v4 } from "uuid"
import { withTranslation } from 'react-i18next'
import { withRouter } from "react-router"
import { Formik, Form as FoForm, Field, ErrorMessage } from 'formik'
import validator from 'validator';
import { toast } from 'react-toastify';

import { GET_LOCATIONS_QUERY } from './queries'

// @flow

import {
  Page,
  Grid,
  Icon,
  Dimmer,
  Badge,
  Button,
  Card,
  Container,
  List,
  Form,
  Table
} from "tabler-react"
import SiteWrapper from "../../SiteWrapper"
import HasPermissionWrapper from "../../HasPermissionWrapper"

import SchoolMenu from "../SchoolMenu"


const ADD_LOCATION = gql`
    mutation CreateSchoolLocation($name: String!, $displayPublic:Boolean!) {
        createSchoolLocation(name: $name, displayPublic: $displayPublic) {
        id
        name
        displayPublic
        }
    }
`;

const return_url = "/school/locations"

const SchoolLocationAdd = ({ t, history }) => (
  <SiteWrapper>
    <div className="my-3 my-md-5">
      <Container>
        <Page.Header title="School" />
        <Grid.Row>
          <Grid.Col md={9}>
          <Card>
            <Card.Header>
              <Card.Title>{t('school.locations.title_add')}</Card.Title>
            </Card.Header>
            <Mutation mutation={ADD_LOCATION} onCompleted={() => history.push(return_url)}> 
                {(addLocation, { data }) => (
                    <Formik
                        initialValues={{ name: '', displayPublic: true }}
                        validate={values => {
                            let errors = {};
                            if (!values.name) {
                            errors.name = t('form.errors.required')
                            } else if 
                                (!validator.isLength(values.name, {"min": 3})) {
                                    errors.name = t('form.errors.min_length_3');
                            }
                            return errors;
                        }}
                        onSubmit={(values, { setSubmitting }) => {
                            addLocation({ variables: {
                                name: values.name, 
                                displayPublic: values.displayPublic
                            }, refetchQueries: [
                                {query: GET_LOCATIONS_QUERY, variables: {"archived": false }}
                            ]})
                            .then(({ data }) => {
                                console.log('got data', data);
                                toast.success((t('school.locations.toast_add_success')), {
                                    position: toast.POSITION.BOTTOM_RIGHT
                                  })
                              }).catch((error) => {
                                toast.error((t('toast_server_error')) + ': ' +  error, {
                                    position: toast.POSITION.BOTTOM_RIGHT
                                  })
                                console.log('there was an error sending the query', error);
                              })
                        }}
                        >
                        {({ isSubmitting, errors, values }) => (
                            <FoForm>
                                <Card.Body>
                                    {/* <Form.Group label={t('school.location.public')}>
                                      <Field type="checkbox" name="displayPublic" checked={values.displayPublic} />
                                      <ErrorMessage name="displayPublic" component="div" />        
                                    </Form.Group> */}
                                    <Form.Group>
                                      <Form.Label className="custom-switch">
                                        <Field 
                                          className="custom-switch-input"
                                          type="checkbox" 
                                          name="displayPublic" 
                                          checked={values.displayPublic} />
                                        <span className="custom-switch-indicator" ></span>
                                        <span className="custom-switch-description">{t('school.location.public')}</span>
                                      </Form.Label>
                                      <ErrorMessage name="displayPublic" component="div" />   
                                    </Form.Group>    

                                    <Form.Group label={t('school.location.name')}>
                                      <Field type="text" 
                                              name="name" 
                                              className={(errors.name) ? "form-control is-invalid" : "form-control"} 
                                              autoComplete="off" />
                                      <ErrorMessage name="name" component="span" className="invalid-feedback" />
                                    </Form.Group>
                                </Card.Body>
                                <Card.Footer>
                                    <Button 
                                      color="primary"
                                      className="pull-right" 
                                      type="submit" 
                                      disabled={isSubmitting}
                                    >
                                      {t('submit')}
                                    </Button>
                                    <Button color="link" onClick={() => history.push(return_url)}>
                                        {t('cancel')}
                                    </Button>
                                </Card.Footer>
                            </FoForm>
                        )}
                    </Formik>
                )}
                </Mutation>
          </Card>
          </Grid.Col>
          <Grid.Col md={3}>
            <HasPermissionWrapper permission="add"
                                  resource="schoollocation">
              <Button color="primary btn-block mb-6"
                      onClick={() => history.push(return_url)}>
                <Icon prefix="fe" name="chevrons-left" /> {t('back')}
              </Button>
            </HasPermissionWrapper>
            <SchoolMenu active_link='schoollocation'/>
          </Grid.Col>
        </Grid.Row>
      </Container>
    </div>
  </SiteWrapper>
);

export default withTranslation()(withRouter(SchoolLocationAdd))