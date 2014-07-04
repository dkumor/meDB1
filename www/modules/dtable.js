
define([],function() {
table_html = '<h4>Recent Data</h4>\
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
          </div>'
dtable = {
    divid: "",
    init: function(divid,opt) {
        dtable.divid = divid;
        dtable.setopt(opt);
    },
    setopt: function(opt) {
        
        for (o in opt) {
            switch (o) {
                case "data":
                    
                    tb = opt[o];
                    
                    //Set visible or invisible based upon amount of data
                    if (tb.length >=1) {
                        meDB.setLocation({i: dtable.divid, v: true})
                    } else {
                        meDB.setLocation({i: dtable.divid, v: false})
                    }
                    
                    addhtml = "";
                    for (i = 0; i < tb.length; ++i) {
                        
                        utctime = new Date(tb[i].time + " UTC");
                        timestring = (utctime.getMonth() + 1) + "/" + utctime.getDate() + "/" + utctime.getFullYear() + " " + utctime.getHours() + ":" + utctime.getMinutes();
                        
                        addhtml += "<tr><td>" + timestring + "</td><td>" + tb[i].label + "</td><td>" + tb[i].value + "</td></tr>"
                    }
                    recentData_ = table_html.replace("{{ELEMENTS}}", addhtml)
                    recentData_ = recentData_.replace("{{TID}}", "resultTable")
                    $("#"+dtable.divid+" .pg").html(recentData_);
                    break;
                default:
                    console.log("Unrecognized: "+o);
                    break;
            }
        }
    },
    resize: function() {
        
    }
}
return dtable;
});
