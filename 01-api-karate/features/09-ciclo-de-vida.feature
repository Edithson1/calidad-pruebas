@local
Feature: Alta, búsqueda, paginación, descarga y borrado completo de imágenes de prueba

  Scenario: CIC-01 Dos imágenes propias aparecen en el catálogo y se eliminan de PostgreSQL, FAISS y S3
    * def ownedImages = []
    * configure afterScenario = read('file:helpers/cleanup-upload.js')
    * def session = call read('file:helpers/login.feature')
    * def auth = session.bearerHeader
    * def before = call read('file:helpers/read-health.feature')
    * def storedBefore = call read('file:helpers/read-storage.feature')
    * def uploadSchema = read('file:schemas/upload-response.json')
    * def filenameA = newFixtureName()
    * def filenameB = newFixtureName()
    * def description = 'a photo of an African elephant'

    When def first = call read('file:helpers/post-upload.feature') { fixtureName: '#(filenameA)', fields: { description: '#(description)' } }
    * eval if (first.uploaded && first.uploaded.filename === filenameA && first.uploaded.image_id) ownedImages.push(first.uploaded.image_id)
    Then match first.uploadStatus == 200
    And match first.uploadType contains 'application/json'
    And match first.uploaded == uploadSchema
    And match first.uploaded contains { success: true, status: 'completed', image_id: '#uuid', filename: '#(filenameA)', similarity_score: '#number', required_similarity: null, banned_words: null, rejection_reason: null }
    And assert first.uploaded.similarity_score >= before.health.similarity_threshold
    And assert first.uploadTime <= limits.upload
    * def idA = first.uploaded.image_id

    When def second = call read('file:helpers/post-upload.feature') { fixtureName: '#(filenameB)', fields: {} }
    * eval if (second.uploaded && second.uploaded.filename === filenameB && second.uploaded.image_id) ownedImages.push(second.uploaded.image_id)
    Then match second.uploadStatus == 200
    And match second.uploadType contains 'application/json'
    And match second.uploaded == uploadSchema
    And match second.uploaded contains { success: true, status: 'completed', image_id: '#uuid', filename: '#(filenameB)', similarity_score: null, required_similarity: null, banned_words: null, rejection_reason: null }
    And assert second.uploadTime <= limits.upload
    * def idB = second.uploaded.image_id
    And match idB != idA

    * def latest = call read('file:helpers/admin-page.feature') { pageSize: 1, pageOffset: 0 }
    * def previous = call read('file:helpers/admin-page.feature') { pageSize: 1, pageOffset: 1 }
    And match latest.page.images[0] contains { id: '#(idB)', filename: '#(filenameB)', description: null }
    And match previous.page.images[0] contains { id: '#(idA)', filename: '#(filenameA)', description: '#(description)' }
    And match previous.page.images[0].metadata.similarity_score == first.uploaded.similarity_score
    And match latest.page.total == before.health.images_in_db + 2
    And match previous.page.total == latest.page.total
    * def pastEnd = call read('file:helpers/admin-page.feature') { pageSize: 1, pageOffset: '#(latest.page.total)' }
    And match pastEnd.page.images == []
    * def afterUploads = call read('file:helpers/read-health.feature')
    And match afterUploads.health.vectors_in_index == before.health.vectors_in_index + 2

    Given url baseUrl
    And path 'api', 'search', 'image'
    And multipart file image = { read: 'file:data/elefante.jpg', filename: 'consulta.jpg', contentType: 'image/jpeg' }
    And multipart field limit = '10'
    And multipart field threshold = '0.95'
    When method post
    Then status 200
    And match header Content-Type contains 'application/json'
    And assert responseTime <= limits.inference
    * def checked = call read('file:helpers/check-search.feature') { payload: '#(response)', requestedLimit: 10, minimumScore: 0.95 }
    * def foundIds = karate.map(response.results, function(item){ return item.id })
    And match foundIds contains [ '#(idA)', '#(idB)' ]

    * def original = call read('file:helpers/download-jpeg.feature') { resource: 'images', imageId: '#(idA)' }
    * def thumbnail = call read('file:helpers/download-jpeg.feature') { resource: 'thumbnails', imageId: '#(idA)' }
    * def metadata = previous.page.images[0].metadata
    And match original.dimensions == { width: '#(metadata.width)', height: '#(metadata.height)' }
    And assert Math.max(thumbnail.dimensions.width, thumbnail.dimensions.height) <= 256
    And assert thumbnail.dimensions.width <= original.dimensions.width && thumbnail.dimensions.height <= original.dimensions.height

    When def removed = call read('file:helpers/delete-owned.feature') { ownedImageId: '#(idA)' }
    Then match removed.deletionStatus == 200
    And match removed.deletionType contains 'application/json'
    And match removed.deletion == { success: true, message: '#string? _.includes(filenameA)', deleted_from: '#[3] #string' }
    And match removed.deletion.deleted_from contains only ['postgresql', 'faiss', 'minio']
    And assert removed.deletionTime <= limits.transfer

    Given url baseUrl
    And path 'api', 'images', idA
    When method get
    Then status 404
    And match response == { detail: 'Imagen no encontrada' }
    And assert responseTime <= limits.fast

    Given path 'api', 'thumbnails', idA
    When method get
    Then status 404
    And match response == { detail: 'Imagen no encontrada' }
    And assert responseTime <= limits.fast
    * def repeated = call read('file:helpers/delete-owned.feature') { ownedImageId: '#(idA)' }
    And match repeated.deletionStatus == 404
    And match repeated.deletion == { detail: 'Imagen no encontrada' }

    Given path 'api', 'search', 'image'
    And multipart file image = { read: 'file:data/elefante.jpg', filename: 'consulta.jpg', contentType: 'image/jpeg' }
    And multipart field limit = '10'
    And multipart field threshold = '0.95'
    When method post
    Then status 200
    And assert responseTime <= limits.inference
    * def checked = call read('file:helpers/check-search.feature') { payload: '#(response)', requestedLimit: 10, minimumScore: 0.95 }
    * def survivingIds = karate.map(response.results, function(item){ return item.id })
    And match survivingIds contains idB
    And match survivingIds !contains idA

    * def remaining = call read('file:helpers/admin-page.feature') { pageSize: 1, pageOffset: 0 }
    And match remaining.page.images[0].id == idB
    And match remaining.page.total == before.health.images_in_db + 1
    * def removedB = call read('file:helpers/delete-owned.feature') { ownedImageId: '#(idB)' }
    And match removedB.deletionStatus == 200
    And match removedB.deletion.deleted_from contains only ['postgresql', 'faiss', 'minio']
    And assert removedB.deletionTime <= limits.transfer
    * def finalHealth = call read('file:helpers/read-health.feature')
    * def finalStorage = call read('file:helpers/read-storage.feature')
    And match finalHealth.health.images_in_db == before.health.images_in_db
    And match finalHealth.health.vectors_in_index == before.health.vectors_in_index
    And match finalStorage.storage.images_bucket_count == storedBefore.storage.images_bucket_count
    And match finalStorage.storage.thumbnails_bucket_count == storedBefore.storage.thumbnails_bucket_count
    * def ownedImages = []
