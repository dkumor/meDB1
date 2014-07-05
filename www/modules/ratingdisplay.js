function ratingdisplay_click(divid,label,value) {
    console.log(divid+label+value)
    meDB.send(divid,{a: [{l: label, v: value}]});
}

define([],function() { return function(divid,initopt) {
    
    loadCss("/modules/ratingdisplay.css");
    /*
    star = '<tr><td><strong>{{LABEL}}</strong></td><td class="rating">\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="10"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="9"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="8"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="7"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="6"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="5"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="4"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="3"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="2"><i></i>\
 <input type="radio" name="r{{ITER}}{{DIVID}}" value="1"><i></i>\
</td></tr>'
    star = star.replace(new RegExp("{{DIVID}}".replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1"),"g"),divid);
    */
    this.ratings = [];
    
    //Remakes the contents of the module
    this.remake = function() {
        totalhtml = "";
        for (i = 0; i < this.ratings.length; ++i) {
            label = this.ratings[i][0];
            stars = this.ratings[i][2]/this.ratings[i][1];
            
            istar = '<h4>'+label+'</h4><div id="rater'+i+divid+'" class="rating" onmouseout="$(\'.rating-hover-fill\').width(\'0%\');"><span class="rating-hover-fill"></span><span class="rating-fill" style="width: '+Math.round(stars*10)+'%"></span>';
            
            for (j=1; j <= 10; ++j) {
                istar += '<input type="radio" name="r'+i+divid+'" value="'+j+'" onmouseover="$(\'#rater'+i+divid+' .rating-hover-fill\').width(\''+(j*10)+'%\')" onclick="ratingdisplay_click(\''+divid+"','"+label+"',"+j+')" /><i></i>';
            }
            
            istar += '</div>&nbsp;&nbsp;&nbsp; ('+this.ratings[i][1]+')';
            if (i < this.ratings.length-1) istar += '<hr />'
            //istar = star.replace(new RegExp("{{ITER}}".replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1"),"g"),i).replace("{{LABEL}}",label);
            
            totalhtml+= istar;
        }
        totalhtml += "</table>";
         $("#"+divid+" .pg").html(totalhtml);
        //Set visible or invisible based upon amount of data
        if (this.ratings.length >=1) {
            meDB.setLocation({i: divid, v: true})
        } else {
            meDB.setLocation({i: divid, v: false})
        }
    };
    
    //Here we define the necessary functions
    this.resize = function() {
        //Nothing to do on resize
    }
    this.setopt = function(opt) {
        
        for (o in opt) {
            switch (o) {
                case "data":
                    this.ratings = opt[o];
                    this.remake();
                    break;
                default:
                    console.log("Unrecognized: "+o);
                    break;
            }
        }
    };
    this.setopt(initopt)
    
};});
