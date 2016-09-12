'use strict';

/**
 * @ngdoc overview
 * @name cubeApp
 * @description
 * # cubeApp
 *
 * Main module of the application.
 */
angular
  .module('cubeApp', [
    'ngAnimate',
    'ngCookies',
    'ngResource',
    'ngRoute',
    'ngSanitize',
    'ngMaterial',
    'ui.router'
  ])
  .config(['$stateProvider',
    function($stateProvider) {
      $stateProvider
        .state('about', {
          url: '/about',
          views: {
            mainModule: {
              templateUrl: 'views/about.html',
              controller: 'AboutCtrl',
              controllerAs: 'about'
            },
            
          }
        })
        .state('main', {
          url: '/',
          views: {
            mainModule: {
              templateUrl: 'views/main.html',
              controller: 'MainCtrl',
              controllerAs: 'main'
            },
            'right@main': {
                templateUrl: 'views/right.html',
                controller: 'RightCtrl',
                controllerAs: 'right'
            },
            'left@main': {
                templateUrl: 'views/left.html',
                controller: 'LeftCtrl',
                controllerAs: 'left'
            }
          }
        });
  }])
  .config(['$stateProvider','$urlRouterProvider',
      function myAppConfig($stateProvider , $urlRouterProvider) {
          $urlRouterProvider.otherwise('/');
  }])
  .value('globals', {
    CHUNK_SIZE: new THREE.Vector3(2128,2128,1),
    CUBE_SIZE: new THREE.Vector3(2128,2128,64),
    HOSTNAME: 'http://localhost',
    dataset: 'small_piriform'
  });
