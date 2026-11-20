@ignore
Feature: Aserciones reutilizables de búsqueda de imágenes

  Scenario:
    * configure matchEachEmptyAllowed = true
    * def searchItem = read('file:schemas/search-item.json')
    * def searchResponse = read('file:schemas/search-response.json')
    * match payload == searchResponse
    * match payload.total_count == payload.results.length
    * assert payload.total_count <= requestedLimit
    * def scores = karate.map(payload.results, function(item){ return item.similarity_score })
    * assert scores.every((score, i) => score + 0.000001 >= minimumScore && (i === 0 || scores[i - 1] + 0.000001 >= score))
    * def ids = karate.map(payload.results, function(item){ return item.id })
    * assert new Set(ids).size === ids.length
    * assert payload.results.every(item => item.url === assetOrigin + '/api/images/' + item.id && item.thumbnail_url === assetOrigin + '/api/thumbnails/' + item.id)
