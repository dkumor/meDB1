
recentData = '<div class="dataframe col-xs-12 col-sm-6 col-lg-4">\
      <div class="pg">\
            <h4>Recent Data</h4>\
                <div class="table-responsive">\
            <table class="table table-striped">\
              <thead>\
                <tr>\
                  <th>Date</th>\
                  <th>Label</th>\
                  <th>Value</th>\
                </tr>\
              </thead>\
              <tbody id="{{TID}}">\
                {{ELEMENTS}}\
              </tbody>\
            </table>\
          </div>\
            </div></div>'

addValues = '<div class="col-xs-12 col-sm-6 col-lg-4">\
            <div class="pg">\
            <h3>Add Datapoint</h3>\
            <form id="mainform" role="form" class="form-inline" onsubmit="return addValue(\'#mainform\')">\
                <div class="form-group">\
                <input type="text" class="form-control input_label" placeholder="Label" autofocus/>\
                <input type="text" class="form-control input_value" placeholder="Value"/>\
                </div>\
                <button type="submit" class="btn btn-default">Add</button>\
            </form>\
            {{ELEMENTS}}\
            </div>\
        </div>'


//This function allows parsing of URL parameters -
//http://www.netlobo.com/url_query_string_javascript.html
function gup(nam) {
    nam = nam.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + nam + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(window.location.href);
    if (results == null)
        return "";
    else
        return results[1];
}

$(".row").prepend('<div class="dataframe col-xs-12 col-sm-6 col-lg-4">\
            <div class="pg color_red">\
            <h4>Warning:</h4>\
            <p>The database used to store data is not encrypted at this time. Do not store any personal\
information, or data that you wouldn\'t want people to know.</p>\
</div></div>\
<div class="dataframe col-xs-12 col-sm-6 col-lg-4">\
<div class="pg color_yellow">\
<h4>Note:</h4>\
<p>The search bar is not functional at this time. Furthermore, data may be lost as changes are made to the software and databases. Just be aware of that.</p></div></div>')

$.get("/q", { key: gup("session") }, function (data) {
    console.log(data);
    data = JSON.parse(data)
    tb = data.points;
    addhtml = "";
    for (i = 0; i < tb.length; ++i) {
        addhtml += "<tr><td>"+tb[i].time+"</td><td>"+tb[i].label+"</td><td>"+tb[i].value+"</td></tr>"
    }
    recentData = recentData.replace("{{ELEMENTS}}",addhtml)
    recentData = recentData.replace("{{TID}}", "resultTable")
    $(".row").prepend(recentData);


    addhtml = '<hr />'
               
    labels = data.labels;
    if (labels.length == 0) {
        addValues = addValues.replace("{{ELEMENTS}}", "")
    } else {
        for (i = 0; i < labels.length; ++i) {
            addhtml += '<form id="frm' + i + '" role="form" class="form-inline" onsubmit="return addValue(\'#frm' + i + '\')" ><div class="form-group"><input type="text" class="form-control input_label" value="' + labels[i] + '"/> <input type="text" class="form-control input_value" placeholder="Value..."/></div> <button type="submit" class="btn btn-default">Add</button></form>';
        }
        addValues = addValues.replace("{{ELEMENTS}}", addhtml)
    }
    $(".row").prepend(addValues);
});

function addValue(vid) {
    label = $(vid + " .input_label").val()
    value = $(vid + " .input_value").val()
    console.log("Add label="+label+" value="+value)
    console.log()
    $.post("/q", { key: gup("session"), label: label, value: value }, function (data) {
        console.log("Server response:" + data);
    });
    if (vid == "#mainform") {
        $(vid + " .input_label").val("")
    }
    $(vid + " .input_value").val("")
    return false;
}