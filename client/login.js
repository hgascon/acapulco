$.fn.pVal = function() {
        return this.hasClass('placeholder') ? '' : this.val();
};

username = "";
password = "";
scheme   = "";
host     = "";
port     = "";
  
Async = splunkjs.Async;
utils = splunkjs.Utils;

var jd = "";
var data = "";
var http = new splunkjs.ProxyHttp("/proxy");
var pc 
var service = "";

var updateConnectionInformation = function() {
  username = utils.trim($("#id_username").pVal()) || "admin";
  password = utils.trim($("#id_password").pVal()) || "admin";
  scheme   = utils.trim($("#id_scheme").pVal())   || "https";
  host     = utils.trim($("#id_host").pVal())     || "localhost";
  port     = utils.trim($("#id_port").pVal())     || "8089";
    
  var connectionString = username + " : ****** @ " + scheme + "://" + host + ":" + port;
  $("#signin-dropdown").text(connectionString);
  };
  
$(function() {
  $('input, textarea').placeholder();
  updateConnectionInformation();

  
  $(".dropdown input").click(function(e) {
    e.stopPropagation();
  });
  
  $(".dropdown input").blur(function(e) {
    updateConnectionInformation();
  });

  $("#login-btn").click(function() {
    $("#ko-login").css("display", "none");
    login();
  });
});


function login(){
	service = new splunkjs.Service(http, { 
		scheme: scheme,
		host: host,
		port: port,
		username: username,
		password: password
	});
  // First, we log in
  service.login(function(err, success) {
    // We check for both errors in the connection as well
    // as if the login itself failed.
    if (err || !success) {
        console.log("Error in logging in");
        $("#ko-login").css("display", "block");
        done(err || "Login failed");
        return;
    }
    else{
      console.log("logged correctly!");
      $("#ko-login").css("display", "none");
      $("#acapulco-run").css("display", "block");
      $("#ok-login").css("display", "block");
    }      
 })
};

function getData(){
    $("#zero-data").css("display", "none");
    $("#ok-login").css("display", "none");
    $("#draw-data").css("display", "none");
    $("#done-data").css("display", "none");
    var query;
    var mode=0;
    var size = sld.n_value;
    if (size > 0){
      $("#get-data").css("display", "block");
      if ($("#normal-data").attr("checked") == "checked"){
        query = "" +
        'search index=acapulco_normal sourcetype=acapulco_normal | head '+size+' | fields chan,saddr,sport,dport,daddr,url,hash';
        mode=1;
      }
      else{
        query = "" +
        'search index=acapulco sourcetype=acapulco | head '+size+' | fields chan,saddr,sport,dport,daddr,url,hash';
      }
      service.oneshotSearch(query, {count: 0}, function(err, results) {
        console.log(results);
        if (err) {
          console.log(err);
          alert("An error occurred with the search");
          return;
        }
        $("#get-data").css("display", "none");
        $("#draw-data").css("display", "block");
        parse(results,mode);
      })
    }
    else{
      $("#zero-data").css("display", "block");
    }
};
 