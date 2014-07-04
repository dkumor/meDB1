function adder_submitForm(adder_id,vid) {
    label = $(vid + " .input_label").val();
    value = $(vid + " .input_value").val();
      
    meDB.send(adder_id,{a: [{l: label, v: value}]},"Add datapoint label="+label+" value="+value);
    return false;
}

define([],function() {
adder_html = '<h3>Add Datapoint</h3>\
            <form id="mainform" role="form" class="form-inline" onsubmit="return adder_submitForm(\'{{ID}}\',\'#mainform\')">\
                <div class="form-group">\
                <input type="text" class="form-control input_label" placeholder="Label" autofocus/>\
                <input type="text" class="form-control input_value" placeholder="Value"/>\
                </div>\
                <button type="submit" class="btn btn-default">Add</button>\
            </form>\
            {{ELEMENTS}}'
adder = {
    divid: "",
    init: function(divid,opt) {
        adder.divid = divid;
        adder.setopt(opt);
    },
    setopt: function(opt) {
        
        for (o in opt) {
            switch (o) {
                case "labels":
                    
                    labels = opt[o];
                    addhtml = "<hr />"
                    addValues_ = "";
                    if (labels.length == 0) {
                        addValues_ = adder_html.replace("{{ELEMENTS}}", "")
                    } else {
                        for (i = 0; i < labels.length; ++i) {
                            addhtml += '<form id="frm' + i + '" role="form" class="form-inline" onsubmit="return adder_submitForm(\'{{ID}}\',\'#frm' + i + '\')" ><div class="form-group"><input type="text" class="form-control input_label" value="' + labels[i] + '"/> <input type="text" class="form-control input_value" placeholder="Value..."/></div> <button type="submit" class="btn btn-default">Add</button></form>';
                        }
                        addValues_ = adder_html.replace("{{ELEMENTS}}", addhtml)
                    }
                    $("#"+adder.divid+" .pg").html(addValues_.replace(new RegExp("{{ID}}".replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1"),"g"),adder.divid));
                    break;
                default:
                    console.log("Adder unrecognized: "+o);
                    break;
            }
        }
    },
    resize: function() {
        
    }
}
return adder;
});
