
d3.select("#show-clusters").on("click", showClusters);
d3.select("#hide-clusters").on("click", hideClusters);
d3.select("#hide-ticks").on("click", hideTicks);
d3.select("#show-ticks").on("click", showTicks);
d3.select("#hide-brush").on("click", hideBrush);
d3.select("#show-brush").on("click", showBrush);

var clusterDensity = 0;
var events;

function showClusters() {
  if (d3.selectAll("circle")[0].length == 0){
    if (clusterDensity == 0){
      clusterDensity = readClustersDensity(data)
    }
    drawClusters();
  } 
  d3.selectAll("circle").style("display", null);
};

function hideClusters() {
  d3.selectAll("circle").remove();
  // d3.selectAll("circle").style("display", "none");
};

function hideTicks() {
  //d3.selectAll(".axis g").style("display", "none");
  d3.selectAll(".axis path").style("display", "none");
};

function showTicks() {
  //d3.selectAll(".axis g").style("display", null);
  d3.selectAll(".axis path").style("display", null);
};

function hideBrush() {
  d3.selectAll(".background").style("visibility", "hidden");
};

function showBrush() {
  d3.selectAll(".background").style("visibility", null);
};

var m = [30, 10, 10, 10],
    w = 960 - m[1] - m[3],
    h = 500 - m[0] - m[2];

var x = d3.scale.ordinal().rangePoints([0, w], 1),
    y = {},
    dragging = {};

var line = d3.svg.line(),
    axis = d3.svg.axis().orient("left"),
    background,
    foreground;

var svg;

var colors = {
  "dionaea.capture": [28,100,52],
  "dionaea.dcerpcrequests": [214,55,79],
  "dionaea.capture.anon": [185,56,73],
  "thug.files": [30,100,73],
  "Glastopf.events.in": [359,69,49],
  "cuckoo.analysis": [110,57,70],
  "mwbinary.dionaea.sensorunique": [120,56,40],
  "dionaea.shellcodeprofiles": [1,100,79],
  "glastopf.events.anon": [271,39,57],
  "thug.events": [274,30,76],
  "glastopf.files": [10,30,42],
  "dionaea.capture.in": [10,28,67],
  "glastopf.sandbox": [318,65,67],
  "tip": [334,80,84],
  // "": [37,50,75],
  // "": [339,60,75],
  // "": [56,58,73],
  // "": [339,60,49],
  // "": [325,50,39],
  // "": [20,49,49],
  // "": [60,86,61],
  // "": [185,80,45],
  // "": [189,57,75],
  // "": [41,75,61],
  // "": [204,70,41]
};

function color(d,a) {
  var c = colors[d];
  return ["hsla(",c[0],",",c[1],"%,",c[2],"%,",a,")"].join("");
};

function clean(){
   y = {}
   dragging = {}
   d3.select("svg").remove()
   svg = d3.select("#chart").append("svg:svg")
    .attr("width", w + m[1] + m[3])
    .attr("height", h + m[0] + m[2])
  .append("svg:g")
    .attr("transform", "translate(" + m[3] + "," + m[0] + ")");

}

// var svg = d3.select("body").append("svg:svg")
  // svg = d3.select("svg")
  //   .attr("width", w + m[1] + m[3])
  //   .attr("height", h + m[0] + m[2])
  // .append("svg:g")
  //   .attr("transform", "translate(" + m[3] + "," + m[0] + ")");

function parse(results,mode){
    events = results;
    var rows = results.rows.slice();
    var fields = results.fields.slice();
    jd = "[";
    for(var i = 0; i < rows.length; i++){
      var row = rows[i];
      var e = "{";
      for(var j = 1; j < 6; j++){
        e += "\"" + fields[j] + "\": " + row[j] + ", ";
      }
      e = e.substring(0,e.length - 2) + "}, ";
      jd += e;
    }
    jd = jd.substring(0,jd.length - 2) + "]";  
    data = jQuery.parseJSON(jd);
    // console.log(data);
    console.log("splunk data received!");
    draw(data);
    //if data is not clustered mode=1
    //and clusters are not shown 
    clusterDensity=mode;
};


//TODO 

function readClustersDensity(data){

  var ks = Object.keys(data[0]);
  var cld = {};
  for (k = 0; k < ks.length; k++){
    key = ks[k];
    for (row = 0; row < data.length; row++){
      var label = parseFloat(data[row][key]).toFixed(1);
      if (!cld.hasOwnProperty(key)){
        cld[key] = {};
      }      
      if (!cld[key].hasOwnProperty(label)){
        cld[key][label] = 0;
      }
      cld[key][label] += 1;
    }
  }
  //cld is now a multidimensional object with
  //keys, cluster labels and cluster density
  return cld;
};


function drawClusters(){

  var a = d3.selectAll(".axis")[0];
  for(i=0;i<a.length;i++){
    var axis = d3.select(a[i]);
    var key = axis.property("__data__");
    var g = axis.selectAll("g")[0];
    for(j=0;j<g.length;j++){
      var group = d3.select(g[j]);
      var label = parseFloat(group.select("text").text()).toFixed(1);
      if (clusterDensity[key].hasOwnProperty(label)){
        var size = clusterDensity[key][label];
        // var s = Math.log(size)+20;
        var s = size*115/sld.n_value;
        group.append("svg:circle")
        // .style("stroke", "black")
        .style("fill", "black")
        .style("opacity", "0.5")
        .attr("r", 0)
        .on("mouseover", function(){d3.select(this)
          .style("opacity", "1");})
        .on("mouseout", function(){d3.select(this)
          .style("opacity", "0.5");})
        .transition()
        .delay(100)
        .duration(1000)    
        .attr("r", s)
        .style("fill", "orange");
      }
    }
  }
};


function getDomain(data,d){
  var limits = d3.extent(data, function(p){
    return +p[d];
  })
  if (limits[0] == limits[1]){
    limits[0]--;
    limits[1]++;
  }
  return limits;
}

function draw(data){
  clean();
  console.log("drawing data!");
  // x.domain(dimensions = d3.keys(data[0]).filter(function(d) {
  //   return (y[d] = d3.scale.linear()
  //       .domain(d3.extent(data, function(p) {
  //         return +p[d];
  //       }))
  //       .range([h, 0])
  //       );
  // }));

  x.domain(dimensions = d3.keys(data[0]).filter(function(d) {
    return (y[d] = d3.scale.linear()
        .domain(getDomain(data,d))
        .range([h, 0])
        );
  }));


  // Add grey background lines for context.
  background = svg.append("svg:g")
      .attr("class", "background")
    .selectAll("path")
      .data(data)
    .enter().append("svg:path")
      .attr("d", path);

  // Add blue foreground lines for focus.
  foreground = svg.append("svg:g")
      .attr("class", "foreground")
    .selectAll("path")
      .data(data)
    .enter().append("svg:path")
      .attr("d", path);

  // Add a group element for each dimension.
  var g = svg.selectAll(".dimension")
      .data(dimensions)
    .enter().append("svg:g")
      .attr("class", "dimension")
      .attr("transform", function(d) { return "translate(" + x(d) + ")"; })
      .call(d3.behavior.drag()
        .on("dragstart", function(d) {
          dragging[d] = this.__origin__ = x(d);
          background.attr("visibility", "hidden");
        })
        .on("drag", function(d) {
          dragging[d] = Math.min(w, Math.max(0, this.__origin__ += d3.event.dx));
          foreground.attr("d", path);
          dimensions.sort(function(a, b) { return position(a) - position(b); });
          x.domain(dimensions);
          g.attr("transform", function(d) { return "translate(" + position(d) + ")"; })
        })
        .on("dragend", function(d) {
          delete this.__origin__;
          delete dragging[d];
          transition(d3.select(this)).attr("transform", "translate(" + x(d) + ")");
          transition(foreground)
              .attr("d", path);
          background
              .attr("d", path)
              .transition()
              .delay(500)
              .duration(0)
              .attr("visibility", null);
        }));

  // Add an axis and title.
  g.append("svg:g")
      .attr("class", "axis")
      .each(function(d) { d3.select(this).call(axis.scale(y[d])); })
    .append("svg:text")
      .attr("text-anchor", "middle")
      .attr("y", -9)
      .text(String)

  // Add and store a brush for each axis.
  g.append("svg:g")
      .attr("class", "brush")
      .each(function(d) { d3.select(this).call(y[d].brush = d3.svg.brush().y(y[d]).on("brush", brush)); })
    .selectAll("rect")
      .attr("x", -8)
      .attr("width", 16);

  $("#draw-data").css("display", "none");
  $("#done-data").css("display", "block");
};

function position(d) {
  var v = dragging[d];
  return v == null ? x(d) : v;
}

function transition(g) {
  return g.transition().duration(500);
}

// Returns the path for a given data point.
function path(d) {
  return line(dimensions.map(function(p) { return [position(p), y[p](d[p])]; }));
}

// Handles a brush event, toggling the display of foreground lines.
function brush() {
  var actives = dimensions.filter(function(p) { return !y[p].brush.empty(); }),
      extents = actives.map(function(p) { return y[p].brush.extent(); });
  foreground.style("display", function(d) {
    return actives.every(function(p, i) {
      return extents[i][0] <= d[p] && d[p] <= extents[i][1];
    }) ? null : "none";
  });
}