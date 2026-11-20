@comun
Feature: Autenticación en las rutas protegidas

  Background:
    * url baseUrl

  Scenario Outline: <code> Exige Bearer para <verb> <route>
    * def targetPath = verb === 'delete' ? route + '/' + newId() : route
    Given path targetPath
    When method verb
    Then status 401
    And match header Content-Type contains 'application/json'
    And match header WWW-Authenticate == 'Bearer'
    And match response == { detail: 'No autorizado' }
    And assert responseTime <= limits.fast

    Examples:
      | code    | verb   | route             |
      | AUTH-01 | get    | api/admin/images  |
      | AUTH-02 | get    | api/admin/storage |
      | AUTH-03 | post   | api/upload        |
      | AUTH-04 | delete | api/admin/images  |

  Scenario: AUTH-05 Rechaza un token con formato inválido
    Given path 'api', 'admin', 'images'
    And header Authorization = 'Bearer no-es-un-token-jwt'
    When method get
    Then status 401
    And match header WWW-Authenticate == 'Bearer'
    And match response == { detail: 'No autorizado' }
    And assert responseTime <= limits.fast

  Scenario: AUTH-06 Login con formulario incompleto retorna 422
    Given path 'api', 'admin', 'login'
    And form field username = 'usuario-qa'
    When method post
    Then status 422
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def checked = call read('file:helpers/check-validation.feature') { payload: '#(response)', location: ['body', 'password'], errorType: 'missing' }
