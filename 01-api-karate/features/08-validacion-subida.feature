@local
Feature: Validaciones de subida multipart autenticada

  Background:
    * url baseUrl
    * def session = callonce read('file:helpers/login.feature')
    * def auth = session.bearerHeader
    * def ownedImages = []
    * configure afterScenario = read('file:helpers/cleanup-upload.js')
    * def uploadSchema = read('file:schemas/upload-response.json')

  Scenario: UPL-01 Rechaza archivo de texto aunque el usuario esté autenticado
    Given path 'api', 'upload'
    And header Authorization = auth
    And multipart file image = { value: 'texto de prueba', filename: 'invalido.txt', contentType: 'text/plain' }
    When method post
    Then status 400
    And match header Content-Type contains 'application/json'
    And match response == { detail: 'El archivo debe ser una imagen' }
    And assert responseTime <= limits.fast

  Scenario: UPL-02 Rechaza una imagen con demasiados píxeles
    Given path 'api', 'upload'
    And header Authorization = auth
    And multipart file image = { read: 'file:data/sobre-limite.png', filename: 'sobre-limite.png', contentType: 'image/png' }
    When method post
    Then status 413
    And match header Content-Type contains 'application/json'
    And match response == { detail: '#regex La imagen supera el límite de [0-9]+ píxeles' }
    And assert responseTime <= limits.fast

  Scenario: UPL-03 Exige la parte image
    Given path 'api', 'upload'
    And header Authorization = auth
    And multipart field description = 'una descripción sin archivo'
    When method post
    Then status 422
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.fast
    * def checked = call read('file:helpers/check-validation.feature') { payload: '#(response)', location: ['body', 'image'], errorType: 'missing' }

  Scenario: UPL-04 Una palabra restringida en el nombre retorna el motivo y la palabra detectada
    * def filename = newFixtureName().replace(/\.jpg$/, '-gun.jpg')
    * def outcome = call read('file:helpers/post-upload.feature') { fixtureName: '#(filename)', fields: {} }
    * eval if (outcome.uploaded && outcome.uploaded.filename === filename && outcome.uploaded.image_id) ownedImages.push(outcome.uploaded.image_id)
    Then match outcome.uploadStatus == 422
    And match outcome.uploadType contains 'application/json'
    And match outcome.uploaded == uploadSchema
    And match outcome.uploaded contains { success: false, status: 'rejected', image_id: null, banned_words: ['gun'], rejection_reason: 'banned_words', similarity_score: null, required_similarity: null }
    And assert outcome.uploadTime <= limits.fast

  Scenario: UPL-05 Una descripción que no corresponde retorna la similitud y el umbral
    * def filename = newFixtureName()
    * def description = 'a studio photo of a close-up of a computer microprocessor on a printed circuit board'
    * def outcome = call read('file:helpers/post-upload.feature') { fixtureName: '#(filename)', fields: { description: '#(description)' } }
    * eval if (outcome.uploaded && outcome.uploaded.filename === filename && outcome.uploaded.image_id) ownedImages.push(outcome.uploaded.image_id)
    Then match outcome.uploadStatus == 422
    And match outcome.uploadType contains 'application/json'
    And match outcome.uploaded == uploadSchema
    And match outcome.uploaded contains { success: false, status: 'rejected', image_id: null, banned_words: null, rejection_reason: 'low_similarity', similarity_score: '#number', required_similarity: '#number' }
    And assert outcome.uploaded.similarity_score < outcome.uploaded.required_similarity
    And assert outcome.uploadTime <= limits.inference
