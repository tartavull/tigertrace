'use strict';

/**
 * @ngdoc function
 * @name cubeApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the cubeApp
 */

angular.module('cubeApp')

angular.module('cubeApp')
  .controller('MainCtrl', 
    function ($scope, sceneService,
    tileService, overlayService, 
    meshService, controlService, $window,
    $timeout, $mdSidenav, $log) {


    function resize(event) {
      overlayService.resize();
      sceneService.resize();
      controlService.resize($window.innerWidth, $window.innerHeight)
    };
    $window.addEventListener('resize', resize );
    resize();

    sceneService.cube.add(tileService.planesHolder);
    sceneService.cube.add(meshService.meshes);


    $scope.toggleRight = buildToggler('right');
    $scope.toggleLeft = buildDelayedToggler('left');
    $scope.isOpenLeft = function(){
      return $mdSidenav('left').isOpen();
    };
    /**
     * Supplies a function that will continue to operate until the
     * time is up.
     */
    function debounce(func, wait, context) {
      var timer;
      return function debounced() {
        var context = $scope,
            args = Array.prototype.slice.call(arguments);
        $timeout.cancel(timer);
        timer = $timeout(function() {
          timer = undefined;
          func.apply(context, args);
        }, wait || 10);
      };
    }
    /**
     * Build handler to open/close a SideNav; when animation finishes
     * report completion in console
     */
    function buildDelayedToggler(navID) {
      return debounce(function() {
        // Component lookup should always be available since we are not using `ng-if`
        $mdSidenav(navID)
          .toggle()
          .then(function () {
            $log.debug("toggle " + navID + " is done");
          });
      }, 200);
    }
    function buildToggler(navID) {
      return function() {
        // Component lookup should always be available since we are not using `ng-if`
        $mdSidenav(navID)
          .toggle()
          .then(function () {
            $log.debug("toggle " + navID + " is done");
          });
      }
    }
  });
    
