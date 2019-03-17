// @flow

import React, {Component } from 'react'
import gql from "graphql-tag"
import { Query, Mutation } from "react-apollo";
import { withTranslation } from 'react-i18next'
import { withRouter } from "react-router"
import { toast } from 'react-toastify'

import { GET_CLASSTYPES_QUERY, GET_CLASSTYPE_QUERY } from './queries'
import { CLASSTYPE_SCHEMA } from './yupSchema'

import {
  Page,
  Grid,
  Icon,
  Button,
  Card,
  Container,
  Form,
} from "tabler-react";
import SiteWrapper from "../../SiteWrapper"
import HasPermissionWrapper from "../../HasPermissionWrapper"

import SchoolMenu from "../SchoolMenu"


const UPDATE_CLASSTYPE_IMAGE = gql`
mutation UploadSchoolClasstypeImage($input: UploadSchoolClasstypeImageInput!) {
  uploadSchoolClasstypeImage(input: $input) {
    schoolClasstype {
      id
      archived
      name
      description
      displayPublic
      urlWebsite
      image
    }
  }
}
`


const customFileInputLabelStyle = {
  whiteSpace: "nowrap",
  display: "block",
  overflow: "hidden"
}


class SchoolClasstypeEditImage extends Component {
  constructor(props) {
    super(props)
    console.log("School classtype image edit props:")
    console.log(props)
    this.fileInput = React.createRef()
    // this.fileInputPreview = React.createRef()
  }

  onSubmit(e, id, uploadImage) {
    e.preventDefault()
    const t = this.props.t
    console.log(id)

    console.log(e.target.name + 'clicked')

    var file = this.fileInput.current.files[0]
    console.log(file)
    let reader = new FileReader()

    // console.log(reader.readAsDataURL(file))

    reader.onload = function(reader_event) {
      console.log(reader_event.target.result)
      let b64_enc_image = reader_event.target.result

      uploadImage({ variables: {
        input: {
          id: id,
          image: b64_enc_image
        }
      }, refetchQueries: [
          {query: GET_CLASSTYPES_QUERY, variables: {"archived": false }}
      ]})
      .then(({ data }) => {
          console.log('got data', data)
          toast.success((t('school.classtypes.toast_image_save_success')), {
              position: toast.POSITION.BOTTOM_RIGHT
            })
        }).catch((error) => {
          toast.error((t('toast_server_error')) + ': ' +  error, {
              position: toast.POSITION.BOTTOM_RIGHT
            })
          console.log('there was an error sending the query', error);
        })
      
    }
    reader.readAsDataURL(file)


  }

  // previewFile() {
  //     var preview = this.ref.fileInputPreview.current
  //     var file    = this.fileInput.current.files[0]
  //     var reader  = new FileReader();
    
  //     reader.addEventListener("load", function () {
  //       preview.src = reader.result;
  //     }, false);
    
  //     if (file) {
  //       reader.readAsDataURL(file);
  //     }
  //   }


  render() {
    const t = this.props.t
    const match = this.props.match
    const history = this.props.history
    const id = match.params.id
    const return_url = "/school/classtypes"

    return (
      <SiteWrapper>
        <div className="my-3 my-md-5">
          <Container>
            <Page.Header title="School" />
            <Grid.Row>
              <Grid.Col md={9}>
              <Card>
                <Card.Header>
                  <Card.Title>{t('school.classtypes.edit_image')}</Card.Title>
                  {console.log(match.params.id)}
                </Card.Header>
                <Query query={GET_CLASSTYPE_QUERY} variables={{ id }} >
                {({ loading, error, data, refetch }) => {
                    // Loading
                    if (loading) return <p>{t('loading_with_dots')}</p>
                    // Error
                    if (error) {
                      console.log(error)
                      return <p>{t('error_sad_smiley')}</p>
                    }
                    
                    const initialData = data.schoolClasstype
                    console.log('query data')
                    console.log(data)

                    return (
                      <Mutation mutation={UPDATE_CLASSTYPE_IMAGE} onCompleted={() => history.push(return_url)}> 
                        {(uploadImage, { data }) => (
                          // <Form onSubmit={(event) => this.onSubmit(event)}>
                          
                            <Form autoComplete="off" onSubmit={(event) => this.onSubmit(event, initialData.id, uploadImage)}>
                              <Card.Body>
                                <div className="form-group">
                                  <label className="form-label">{t('custom_file_input_label')}</label>
                                  <div className="custom-file">
                                    <input type="file" ref={this.fileInput} className="custom-file-input" />
                                    <label className="custom-file-label" style={customFileInputLabelStyle}>
                                      {t("custom_file_input_inner_label")}
                                    </label>
                                  </div>
                                </div>
                              </Card.Body>
                              <Card.Footer>
                                <Button 
                                  className="pull-right"
                                  color="primary"
                                  type="submit"
                                >
                                  {t('submit')}
                                </Button>
                                <Button
                                  type="button" 
                                  color="link" 
                                  onClick={() => history.push(return_url)}
                                >
                                    {t('cancel')}
                                </Button>
                                {/* <Button type='submit' value='Submit'>{t('submit')}</Button> */}
                              </Card.Footer>
                              {/* <img ref={this.fileInputPreview} src="" height="200" alt="Image preview..."></img> */}
                            </Form>
                        )}
                      </Mutation>
                    )
                  }}
                </Query>
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
    )}
  }


export default withTranslation()(withRouter(SchoolClasstypeEditImage))