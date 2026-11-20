@ignore
Feature: Aserciones reutilizables de errores 422 de FastAPI

  Scenario:
    * def validationIssue = read('file:schemas/validation-issue.json')
    * match payload == { detail: '#[] validationIssue' }
    * match payload.detail contains deep { loc: '#(location)', type: '#(errorType)' }
