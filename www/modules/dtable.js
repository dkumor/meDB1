
define([],function() { return function(divid,opt) {
    table_html = '<h4>{{TITLE}}</h4>\
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
    this.divid = divid;
    this.title = "Recent Data";
    this.tb= [];
    this.setopt = function(opt) {
        
        for (o in opt) {
            switch (o) {
                case "data":
                    this.tb = opt[o];
                    this.remake();
                    break;
                case "title":
                    this.title = opt[o];
                    this.remake();
                    break;
                default:
                    console.log("Unrecognized: "+o);
                    break;
            }
        }
    };
    this.resize = function() {
        
    };
    
    this.remake = function() {
        //Set visible or invisible based upon amount of data
        if (this.tb.length >=1) {
            meDB.setLocation({i: this.divid, v: true})
        } else {
            meDB.setLocation({i: this.divid, v: false})
        }
        
        addhtml = "";
        for (i = 0; i < this.tb.length; ++i) {
            
            utctime = new Date(this.tb[i].time + " UTC");
            timestring = (utctime.getMonth() + 1) + "/" + utctime.getDate() + "/" + utctime.getFullYear() + " " + utctime.getHours() + ":" + utctime.getMinutes();
            
            addhtml += "<tr><td>" + timestring + "</td><td>" + this.tb[i].label + "</td><td>" + this.tb[i].value + "</td></tr>"
        }
        recentData_ = table_html.replace("{{ELEMENTS}}", addhtml)
        recentData_ = recentData_.replace("{{TID}}", "resultTable").replace("{{TITLE}}",this.title)
        $("#"+this.divid+" .pg").html(recentData_);
    };
    
    
    this.setopt(opt);
    
};});
