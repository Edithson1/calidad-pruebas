@ignore
Feature: Crear una sesión de administrador por formulario URL encoded

  Scenario:
    Given url baseUrl
    And path 'api', 'admin', 'login'
    And form field username = adminUser
    And form field password = adminPassword
    When method post
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def loginSchema = read('file:schemas/login-response.json')
    And assert karate.match(response, loginSchema).pass
    * def bearerHeader = 'Bearer ' + response.access_token
