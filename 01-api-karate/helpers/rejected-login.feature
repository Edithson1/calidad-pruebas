@ignore
Feature: Enviar un intento de autenticación deliberadamente incorrecto en la instancia aislada

  Scenario:
    Given url baseUrl
    And path 'api', 'admin', 'login'
    And form field username = adminUser
    And form field password = newId()
    When method post
    Then status 401
    And match header Content-Type contains 'application/json'
    And match response == { detail: 'Credenciales incorrectas' }
    And assert responseTime <= limits.fast
