@entorno
Feature: Verificar el ejecutor de Karate

  Scenario: Karate interpreta variables y valida un esquema
    * def registro = { id: 1, nombre: 'VisionText' }
    * match registro == { id: '#number', nombre: '#string' }
