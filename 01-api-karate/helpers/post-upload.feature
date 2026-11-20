@ignore
Feature: Enviar un archivo al endpoint de subida

  Scenario:
    Given url baseUrl
    And path 'api', 'upload'
    And header Authorization = auth
    And multipart file image = { read: 'file:data/elefante.jpg', filename: '#(fixtureName)', contentType: 'image/jpeg' }
    And multipart fields fields
    When method post
    * def uploadStatus = responseStatus
    * def uploadTime = responseTime
    * def uploadType = karate.response.header('Content-Type')
    * def uploaded = response
