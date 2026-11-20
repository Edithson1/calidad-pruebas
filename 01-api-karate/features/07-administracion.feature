@local
Feature: Sesión de administrador, almacenamiento y paginación

  Background:
    * url baseUrl

  Scenario: ADM-01 El formulario URL encoded de Android devuelve un JWT Bearer utilizable
    * def session = call read('file:helpers/login.feature')
    * def auth = session.bearerHeader
    * def page = call read('file:helpers/admin-page.feature') { pageSize: 1, pageOffset: 0 }

  Scenario: ADM-02 El formulario multipart de la web devuelve un JWT Bearer utilizable
    Given path 'api', 'admin', 'login'
    And multipart field username = adminUser
    And multipart field password = adminPassword
    When method post
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def loginSchema = read('file:schemas/login-response.json')
    And assert karate.match(response, loginSchema).pass
    * def auth = 'Bearer ' + response.access_token
    * def storage = call read('file:helpers/read-storage.feature')

  Scenario: ADM-03 Rechaza una contraseña incorrecta con 401
    * def checked = call read('file:helpers/rejected-login.feature')

  Scenario Outline: <code> La lista autenticada rechaza <paramName>=<value>
    * def session = callonce read('file:helpers/login.feature')
    * def invalidParams = {}
    * eval invalidParams[paramName] = value
    Given path 'api', 'admin', 'images'
    And header Authorization = session.bearerHeader
    And params invalidParams
    When method get
    Then status 422
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def checked = call read('file:helpers/check-validation.feature') { payload: '#(response)', location: ['query', '#(paramName)'], errorType: '#(error)' }

    Examples:
      | code   | paramName | value | error              |
      | ADM-04 | limit     | 0     | greater_than_equal |
      | ADM-05 | limit     | 501   | less_than_equal    |
      | ADM-06 | offset    | -1    | greater_than_equal |
      | ADM-07 | offset    | abc   | int_parsing        |

  Scenario: ADM-08 El borrado autenticado de un ID aleatorio inexistente devuelve 404
    * def session = callonce read('file:helpers/login.feature')
    Given path 'api', 'admin', 'images', newId()
    And header Authorization = session.bearerHeader
    When method delete
    Then status 404
    And match header Content-Type contains 'application/json'
    And match response == { detail: 'Imagen no encontrada' }
    And assert responseTime <= limits.fast
