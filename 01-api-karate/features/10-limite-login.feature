@limite-login
Feature: Protección temporal del login con una ventana corta en una instancia aislada

  Scenario: RATE-01 Después de agotar los intentos devuelve 429 con Retry-After y luego se recupera
    * def reset = call read('file:helpers/login.feature')
    * def wrongAttempt = function(){ karate.call('file:helpers/rejected-login.feature') }
    * eval karate.repeat(loginAttempts, wrongAttempt)

    Given url baseUrl
    And path 'api', 'admin', 'login'
    And form field username = adminUser
    And form field password = adminPassword
    When method post
    Then status 429
    And match header Content-Type contains 'application/json'
    And match header Retry-After == '#regex [1-9][0-9]*'
    And assert Number(karate.response.header('Retry-After')) <= loginWindowSeconds
    And match response == { detail: '#regex Demasiados intentos fallidos\\..+' }
    And assert responseTime <= limits.fast

    * configure retry = { count: '#(loginWindowSeconds + 4)', interval: 1000 }
    Given path 'api', 'admin', 'login'
    And form field username = adminUser
    And form field password = adminPassword
    And retry until responseStatus === 200
    When method post
    Then status 200
    * def loginSchema = read('file:schemas/login-response.json')
    And assert karate.match(response, loginSchema).pass
