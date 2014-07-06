
define([],function() { return function(divid,initopt) {
    
    this.display = false;
    
    this.locate = function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                latitude = position.coords.latitude;
                longitude = position.coords.longitude;
                meDB.send(divid,{a: [{lat: latitude,long: longitude,accuracy: position.coords.accuracy}]},"location("+latitude+","+longitude+")");
            });
        }
    }
    
    
    this.interval = null;   //The interval at which to send location
    
    this.refresh = function(rate) {
        console.log("Setting refresh: "+rate);
        
        if (this.interval) {
            clearInterval(this.interval);
        }
        if (rate != 0) {
            this.interval = setInterval(this.locate,rate);
        }
    }
    
    //Here we define the necessary functions
    this.resize = function() {
        //Nothing to do on resize
    }
    this.setopt = function(opt) {
        
        for (o in opt) {
            switch (o) {
                case "locate":
                    this.locate();
                    break;
                case "refresh":
                    
                    this.refresh(opt["refresh"]);
                    break;
                case "display":
                    console.log("Unimplemented");
                default:
                    console.log("Unrecognized: "+o);
                    break;
            }
        }
    };
    
    
    this.locate();
    
    this.setopt(initopt)
    
};});
