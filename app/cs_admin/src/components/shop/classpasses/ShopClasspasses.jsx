// @flow

import React, {Component } from 'react'
import { withTranslation } from 'react-i18next'
import { withRouter } from "react-router"
import { useQuery } from '@apollo/react-hooks'
import { Link } from 'react-router-dom'

import {
  Icon,
  List
} from "tabler-react";
import ShopClasspassesBase from "../ShopCLasspassesBase"

import { GET_ORGANIZATION_CLASSPASSES_QUERY } from "./queries"


function ShopClasspasses({ t, match, history }) {
  const title = t("shop.home.title")
  const { loading, error, data } = useQuery(GET_ORGANIZATION_CLASSPASSES_QUERY)

  if (loading) return (
    <ShopClasspassesBase title={title} >
      {t("general.loading_with_dots")}
    </ShopClasspassesBase>
  )
  if (error) return (
    <ShopClasspassesBase title={title}>
      {t("shop.classpasses.error_loading")}
    </ShopClasspassesBase>
  )


  return (
    <ShopClasspassesBase title={title}>
        Classpasses here...
    </ShopClasspassesBase>
  )
}


export default withTranslation()(withRouter(ShopClasspasses))