function() {
  var ids = karate.get('ownedImages', []);
  if (ids.length && karate.get('auth')) {
    ids.forEach(function(id) {
      var cleanup = karate.call('file:helpers/delete-owned.feature', { ownedImageId: id });
      if (cleanup.deletionStatus !== 200 && cleanup.deletionStatus !== 404) {
        karate.fail('Falló la limpieza de la imagen de Karate ' + id + ' con HTTP ' + cleanup.deletionStatus);
      }
    });
  }
}
