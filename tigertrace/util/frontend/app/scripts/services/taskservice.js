'use strict';

/**
 * @ngdoc service
 * @name cubeApp.taskService
 * @description
 * # taskService
 * Service in the cubeApp.
 */
angular.module('cubeApp')
  .service('taskService', function (globals,$http) {
    // AngularJS will instantiate a singleton by calling "new" on this function

    var srv = {
      server: globals.HOSTNAME + ':8888',
      current_edge: null
    };


    srv.getNextEdge = function(callback) {

      $http({
        method: 'GET',
        url: srv.server+ '/dataset/' + globals.dataset +'/edges',
      }).then(function successCallback(response) {
          // this callback will be called asynchronously
          // when the response is available
          srv.current_edge = response.data;
          callback(response.data);

        }, function errorCallback(response) {
          console.error(response);
      });
    };

    srv.submitEdgeDecision = function( decision , callback ) {

      if (srv.current_edge == null) {
        srv.getNextEdge(callback);
        return
      }
      
      $http({
        method: 'POST',
        url: srv.server+ '/dataset/' + globals.dataset +'/edges',
        data: { 'edge': srv.current_edge.edge , 'answer': decision }
      }).then(function successCallback(response) {
          srv.current_edge = response.data;
          callback(response.data);
        }, function errorCallback(response) {
          console.error(response);
      });
    };

    return srv;
  });
