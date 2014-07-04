//The database is controlled through the server's commands.
var meDB = {
    objects: {},            //Array of objects that the application controls.
    sessionID: "",          //The session ID is there to allow reconnect without reinitialization if connection dropped
    socket: null,           //A websocket object used for communicating with the server
    
    init: function() {
        
        //Set the sessionID from the header
        meDB.sessionID = meDB.parseparam("session")
        if (meDB.sessionID.length == 0) {
            window.location.replace('/login');
        }
        
        //Send Init statement to ask for commands
        meDB.sendPing();
        
        //Window focus and blur
        $(window).focus(function() {
            meDB.send("@",{"f": true},"Window focused");
        }).blur(function() {
            meDB.send("@",{"f": false},"Window unfocused");
        });
        
        //On window resize, send window resize event
        var resize_timeout = null;
        $(window).resize(function() {
            clearTimeout(resize_timeout);
            resize_timeout = setTimeout(function() {
                meDB.sendWindowSize();
                meDB.resize();
            },200);
        });
        
        //This is one thing that will take vast quantities of bandwidth.
        //  Every single keypress can be sent to the server if it enables keybinding.
        //  Also, meDB maintains a keymap where it prevents the default action
        //  or runs a function
        $(document).bind('keydown', function(e) {
            
            //Create a key object
            var key = {"n": e.which,"s":e.shiftKey,"c":e.ctrlKey,"a":e.altKey};
            
            //First, send the keypress to the server if keylogging enabled
            if (meDB.keylogger) {
                meDB.send("@",{"k":key},
                        "Key ("+e.which.toString()+")")
            }
            
            //Next, see if there is a binding associated with the key
            var keybind = meDB.getKeyBind(key);
            
            if (keybind) {
                //A keybinding exists, so act upon it
                if (keybind.preventDefault==true) e.preventDefault();
                if (keybind.send && !meDB.keylogger) { 
                    meDB.send("@",{"k":key},
                        "Key ("+e.which.toString()+")")
                }
                if (keybind.func) keybind.func();
            }
        });
        
        //On window close, notify server to delete session
        $(window).unload(function() {
            //The function must be synchronous, so we manually do it
            $.ajax({
                type: 'POST',
                async: false,
                url: meDB.post_url,
                data: {session: meDB.sessionID,q: JSON.stringify({i: "@",d: {close: true}})}
            });
            
        });
        
    },
    
    actions: {},    //Dictionary of actions and functions to run upon the actions
    action: function(name) {
        meDB.send("@",{action: name},"Action(\""+name+"\")");
        
        //Run function on action
        if (name in meDB.actions) {
            meDB.actions[name]();
        }
    },
    
    //Embed the given module (javascript file) in the div divid, giving it setup data opt
    //This creates a box of content.
    embed: function(divid,module,opt) {
        meDB.log("Objects <=: new("+divid+","+module+")");
        
        //If the given div already has a module associated with it, close the module!
        if (meDB.objects[divid]) {
            meDB.log("Objects :=> \""+divid+"\" already exists!");
            meDB.delete(divid);
        }
        objid = divid;
        if (divid.charAt(0)=='#') {
            objid = objid.substr(1);
        }
        //Create a new invisible div with the given ID
        var element = $('<div class="cols-xs-12 col-sm-6 col-lg-4"></div>').attr('id',objid).hide().append('<div class="pg"></div>');
        
        //Add the div to the end of the page
        $("#pg").append(element);
        require([ module ],function(mod) {
            meDB.objects[divid]=mod;
            mod.init(divid,opt);
        });
    },
    //This deletes a box of content
    delete: function(divid) {
        if (meDB.objects[divid]) {
            meDB.log("Objects <=: delete("+divid+")");
            
            //Close the module
            meDB.objects[divid].close();
            
            //Remove the associated element
            $(divid).remove();
        }
    },
    counter: 0,
    getUniqueNumber: function() {
        return meDB.counter++;
    },
    
    log: function(text,loglevel) {
        if (!loglevel) loglevel=0;
                
        //For debug purposes
        if (loglevel >= 2) console.error(text);
        else console.log(text)
    },
    
    //The equivalent of a BSOD or kernel panic
    explode: function(err) {
        text = "Critical Failure\n\n"
        text = text +'Error: '+err+'\n\nLog:\n';
        
        for (i=meDB.logarray.length-1;i>=meDB.logarray.length-30 && i>=0;i--) {
            text= text+meDB.logarray[i][0]+'\n';
        }
        
        alert(text)
    },
    
    connect_failures: 0,        //Number of times in a row that there was a failure to connect
    connect_failmax: 5,         //The maximum number of failures tolerated before falling back
    connect_connected: false,   //Whether or not there is currently an established connection
    connect_wanted: false,      //Whether the websocket connection is something that is wanted
    connect_retrying: false,    //Whether or not we are currently waiting for a connection retry
    connect_url: "wss://"+window.location.host+"/ws/",  //The URL to use for connecting websockets
    
    //Connects to the server using a websocket
    connectSocket: function() {
        url = meDB.connect_url+meDB.sessionID   //The session ID is sent to the websocket for validation
        
        meDB.log("Connecting to server '"+url+"'");
        
        meDB.connect_connected = false;
        meDB.connect_retrying= false;
        
        //Close any previous connections
        if (meDB.connection) meDB.connection.close();
        
        //Create a connection
        meDB.connection = new WebSocket(url);
        
        //Now, some error handling:
        meDB.connection.onerror = function() {
            //Checking if retrying connection prevents double-calling onerror
            if (meDB.connect_retrying==false && meDB.connect_wanted==true ) {
                
                meDB.log("Connection error!",2);
                meDB.connect_failures++;
                
                meDB.connect_retrying= true;
                
                if (meDB.connect_failures > meDB.connect_failmax) {
                    meDB.log("Maximum number of connection failures reached. Giving up.",2);
                    meDB.connect_failures = 0;
                } else {
                    //Retry a couple times, see what can be done
                    var retrytime = 3000*meDB.connect_failures;
                    meDB.log("Retrying connection in "+(retrytime/1000).toString()+" seconds");
                    setTimeout(function() { meDB.connectServer(url); },retrytime);
                }
            }
        }
        
        //If the connection is closed, call the function defined above
        meDB.connection.onclose = function() {
            meDB.connect_connected = false;
            meDB.log("Socket closed. Falling back to POST mode.",0)
            //meDB.connection.onerror();
        }
        
        //And now, what happens after the connection is established
        meDB.connection.onopen = function() {
            meDB.log("Socket connection established.");
            meDB.connect_connected = true; //Set the connection-established marker
            meDB.connect_failures=0;       //Reset the connection-error counter
            
            if (!meDB.connect_hadconnect) {
                meDB.connect_hadconnect=true;   
            }
        }
        
        //Handling server-side messages - this needs to be done once for each connection
        meDB.connection.onmessage = function(e) {
            meDB.receive(e.data,"ws");
        }
    
    },
    
    post_url : "/",    //The URL that is used for posting messages to server
    
    //The following functions send relevant pieces of information to the server
    send: function(divid, data, logmsg) {
        if (!logmsg) logmsg = "";
        
        
        message = JSON.stringify({i: divid, d: data});
        
        //If the socket is connected, send using websocket. Otherwise, use POST
        if (meDB.connect_connected) {
            meDB.log('(ws)<- "'+divid+'"  '+logmsg);
            meDB.connection.send(message);
        } else {
            meDB.log('(post)<- "'+divid+'"  '+logmsg);
            $.post(meDB.post_url,{q: message,session: meDB.sessionID},function(data) {meDB.receive(data,"post");});
        }
    },
    //The following function receives data from the server
    receive: function(data,source) {
        if (typeof(source)==='undefined') source = '?';
        /*
                The message protocol is actually pretty simple:
                The websocket sends an object in json. This object
                is what is passed to the setopt function for decoding
        */
        
        msg = JSON.parse(data)
        for (i in msg) {
            meDB.log("("+source+')-> "' +msg[i].i + '"');
            if (msg[i].i=="@") meDB.setopt(msg[i].d);
            else meDB.objects[msg[i].i].setopt(msg[i].d);
        }
    },
    /*
        Set location of the div
        
        t: top
        l: bottom (last)
        a: after given div
        b: before given div
        v: visibility of div
    */
    //Set the given object's location
    setLocation: function(l) {
        meDB.log("Location <=: move("+l.i+")");
        for (q in l) {
            switch (q) {
                case "i":
                    break;  //The id
                case "t":
                    //Set the div to the top
                    $("#"+l.i).prependTo('#pg');
                    break;
                case "l":
                    //Set the div to the bottom
                    $("#"+l.i).appendTo('#pg');
                    break;
                case "a":
                    $("#"+l.i).insertAfter("#"+l[q]);
                    break;
                case "b":
                    $("#"+l.i).insertBefore("#"+l[q]);
                    break;
                case "v":
                    if (l[q]) $("#"+l.i).show();
                    else $("#"+l.i).hide();
                    break;
            }
        }
    },
    
    refresh_interval: null,    //The interval command
    refresh: function(rate) {
        //Clear the refresh interval
        if (meDB.refresh_interval) {
            clearInterval(meDB.refresh_interval);
        }
        if (rate != 0) {
            meDB.refresh_interval = setInterval(meDB.sendPing,rate);
        }
    },
    
    //Send a null message to check for server commands
    sendPing: function() {
        meDB.send("@",{},"Ping");
    },
    
    //Send a hrud message. The format is defined before the "setopt" function
    sendHRUD: function() {        
        meDB.send("@",{
            h: [window.location.href,window.document.referrer],
            r: $(window).width().toString()+'x'+$(window).height().toString(),
            u: navigator.userAgent,
            d: window.screen.width.toString()+'x'+window.screen.height.toString()
                +'x'+window.screen.pixelDepth.toString()+'|'+Date()
        },"HRUD");
    },
    sendWindowSize: function(text) {
        if (!text) text="Window Size";
        meDB.send("@",{'r': $(window).width().toString()+'x'+$(window).height().toString()},
                        text);
    },
    
    //Here is a look-up table for keyboard-sending
    keyboard: [],
    keylogger: false,    //Boolean, whether or not to send all keypresses
    getKeyBind: function(key) {
        if (meDB.keyboard[key.n]) {
            for (i=0;i<meDB.keyboard[key.n].length;i++) {
                if (meDB.keyboard[key.n][i].a==key.a && meDB.keyboard[key.n][i].s==key.s
                    && meDB.keyboard[key.n][i].c==key.c) {
                    return meDB.keyboard[key.n][i];
                }
            }
        }
        return null;
    },
    
    setKeyBind: function(key,preventdefault,funct,send,del) {
        var keyobj = meDB.getKeyBind(key);
        
        if (!keyobj) {
            meDB.log("Keybind <=: new("+key.n+")");
            //Check to see if there is an array declared at the key
            if (!meDB.keyboard[key.n]) {
                meDB.keyboard[key.n]=[];
            }
            //Add keybinding to the array
            meDB.keyboard[key.n].push({ c: key.c, s: key.s, a: key.a,
                        preventDefault: preventdefault, func: funct, send: send});
        } else {
            if (del) {
                meDB.log("Keybind <=: delete("+key.n+")");
                
                //Find the object
                for (i=0;i<meDB.keyboard[key.n].length;i++) {
                    //Remove it
                    if (meDB.keyboard[key.n][i]==keyobj) {
                        meDB.keyboard[key.n].splice(i,1);
                        break;
                    }
                }
                
                //Check for empty-parens, and reset to undefined
                if (meDB.keyboard[key.n].length==0) {
                    meDB.keyboard[key.n]=undefined;
                }
            } else {
                meDB.log("Keybind <=: update("+key.n+")");
                //Just update the links
                keyobj.preventDefault = preventdefault;
                keyobj.func = funct;
                keyobj.send = send;
            }
        }
    },
    
    
    /*meDB Core options:
        Send:
            [Packaged in one command
                h: href - contents of address bar and referrer
                r: window size
                u: user-agent
                d: screen-dimensions+local date (good to use as identifier)
            ]
            
            k: keypress - data regarding keypress
            r: resize of window (also just sending window dimensions) (in CHRUD)
            a: User drag-dropped file, and contents if not localhost
            f: Browser window focused or lost focus
            action: Send action name
            
        Recieve:
            i: set session ID
            c: create object - contains further data
            d: destroy object - contains further data
            l: move objects to location
            t: set title of window
            k: map/change key mapping
            ks: Toggle sending of keystrokes on or off
            r: resize window
            h: send hrudi package
            j: run arbitrary javascript
            ws: Connect/disconnect websocket
            rr: Refresh rate, the rate at which to ping server for updates
            clr: clear all objects
            
    */
    setopt: function(opt) {        
        for (var option in opt) {
            switch (option) {
                case "c":
                    for (k in opt[option]) {
                        var o = opt[option][k];
                        /*
                            Create objects:
                                i: divid of object to create
                                t: type of object (link to javascript module)
                                l: location object for the new div
                                o: Object's options
                        */
                        
                        
                        //Initialize the module and set the object's properties
                        meDB.embed(o.i,o.t,o.o);
                        
                        //Set location/animation of object
                        //meDB.setLocation(o.l);
                    }
                    
                    break;
                    
                case "d":   //Delete the object
                    for (k in opt[option]) {
                        meDB.delete(opt[option][k]);
                    }
                    break;
                case "l":
                    //Location of object
                    for (k in opt[option]) {
                        meDB.setLocation(opt[option][k]);
                    }
                    break;
                case "k":
                    var key = opt[option];
                    //Keybindings come in arrays
                    for (k in key) {
                        meDB.setKeyBind(key[k].k,key[k].p,null,key[k].s,key[k].d);
                    }
                    break;
                case "ks":
                    meDB.log("Send Keystrokes <=: "+opt[option]);
                    meDB.keylogger = opt[option];
                    break;
                case "t":
                    meDB.log('Window Title <=: "'+opt[option]+'"');
                    document.title = opt[option];
                    break;
                case "i":
                    meDB.log('Session ID <=: "'+opt[option]+'"');
                    meDB.sessionID = opt[option];
                    break;
                case "h":
                    meDB.sendHRUDI();
                    break;
                case "r":
                    meDB.log('Window Size <=: "'+opt[option]+'"');
                    window.resizeTo(opt[option].w,opt[option].h);
                    break;
                case "j":
                    meDB.log('Executing javascript from server');
                    try {
                        eval(opt[option]);
                    } catch (err) {
                        meDB.log('ERROR executing server-sent javascript!',10);
                    }
                    break;
                case "clr":
                    for (k in meDB.objects) {
                        meDB.delete(k);
                    }
                    break;
                case "ws":
                    meDB.connect_wanted = opt[option];
                    if (meDB.connect_wanted && !meDB.connect_connected) meDB.connectSocket();
                    break;
                case "rr":
                    meDB.log('Refresh Rate <=: '+ opt[option]);
                    meDB.refresh(opt[option]);
                    break;
                default:
                    meDB.log("Server command not recognized",10);
            }
        }
        
        
    },
    //Tell all containers to resize
    resize: function() {
        for (obj in meDB.objects) {
            meDB.objects[obj].resize();
        }
    },
    
    //This function allows parsing of URL parameters in javascript-
    //http://www.netlobo.com/url_query_string_javascript.html
    parseparam: function( nam ) {
      nam = nam.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
      var regexS = "[\\?&]"+nam+"=([^&#]*)";
      var regex = new RegExp( regexS );
      var results = regex.exec( window.location.href );
      if( results == null )
        return "";
      else
        return results[1];
    },
    
}

meDB.init();
