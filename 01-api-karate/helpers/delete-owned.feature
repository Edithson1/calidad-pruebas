@ignore
Feature: Borrar una imagen creada durante el escenario

  Scenario:
    * match ownedImageId == '#uuid'
    Given url baseUrl
    And path 'api', 'admin', 'images', ownedImageId
    And header Authorization = auth
    When method delete
    * def deletionStatus = responseStatus
    * def deletionTime = responseTime
    * def deletionType = karate.response.header('Content-Type')
    * def deletion = response
