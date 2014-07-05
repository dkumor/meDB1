function adder_submitForm(adder_id,vid) {
    label = $(vid + " .input_label").val();
    value = $(vid + " .input_value").val();
    $(vid + " .input_value").val("")
    $(vid + " .input_label").val("");
    meDB.send(adder_id,{a: [{l: label, v: value}]},"Add datapoint label="+label+" value="+value);
    return false;
}

define([], function() {
    return function(divid,opt) {
    this.adder_html = '<h3>{{TITLE}}</h3>\
                <form id="mainform'+divid+'" role="form" class="form-inline" onsubmit="return adder_submitForm(\'{{ID}}\',\'#mainform'+divid+'\')">\
                    <div class="form-group">\
                    <input type="text" class="form-control input_label" placeholder="Label" autofocus/>\
                    <input type="text" class="form-control input_value" placeholder="Value"/>\
                    </div>\
                    <button type="submit" class="btn btn-default">Add</button>\
                </form>\
                {{ELEMENTS}}';
    this.divid = divid;
    this.labels = [];
    this.title = "Add Datapoint";
    this.setopt = function(opt) {
        
        for (o in opt) {
            switch (o) {
                case "labels":
                    
                    this.labels = opt[o];
                    this.remake();
                    break;
                case "title":
                    this.title = opt[o];
                    this.remake();
                    break;
                default:
                    console.log("Adder unrecognized: "+o);
                    break;
            }
        }
    };
    this.resize = function() {
        
    };
    
    this.remake = function() {
        addhtml = "<hr />"
        addValues_ = "";
        if (this.labels.length == 0) {
            addValues_ = this.adder_html.replace("{{ELEMENTS}}", "")
        } else {
            for (i = 0; i < this.labels.length; ++i) {
                addhtml += '<form id="frm' +this.divid+ i + '" role="form" class="form-inline" onsubmit="return adder_submitForm(\'{{ID}}\',\'#frm' + this.divid+i + '\')" ><div class="form-group"><input type="text" class="form-control input_label" value="' + this.labels[i] + '"/> <input type="text" class="form-control input_value" placeholder="Value..."/></div> <button type="submit" class="btn btn-default">Add</button></form>';
            }
            addValues_ = this.adder_html.replace("{{ELEMENTS}}", addhtml)
        }
        $("#"+this.divid+" .pg").html(addValues_.replace(new RegExp("{{ID}}".replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1"),"g"),this.divid).replace("{{TITLE}}",this.title));
    };
    
    this.setopt(opt);
    meDB.setLocation({i: this.divid, v: true});
    
};});
