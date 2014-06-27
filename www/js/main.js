var meDB = {
    sessionID: 0,           //The session ID is there to allow reconnect without reinitialization if connection dropped
    connection: null,           //A websocket object used for communicating with the server
    connect_failures: 0,        //Number of times in a row that there was a failure to connect
    connect_failmax: 5,         //The maximum number of failures tolerated before falling back
    connect_connected: false,   //Whether or not there is currently an established connection
    connect_hadconnect: false,  //Whether there ever was a successful connection
    
    //Connects to the server using a websocket
    connectServer: function(url) {
        console.log("Connecting to server '"+url+"'");
        
        meDB.connect_connected = false;
        
        //Close any previous connections
        if (meDB.connection) meDB.connection.close();
        
        //Create a connection
        meDB.connection = new WebSocket(url);
        
        //Now, some error handling:
        meDB.connection.onerror = function() {
            console.error("Connection error!");
            meDB.connect_failures++;
            
            if (meDB.connect_failures > meDB.connect_failmax) {
                console.error("Maximum number of connection failures reached. Giving critical error.");
                //meDB.connect_failures = 0;
                //meDB.criticalError("Server connection failed");
            } else {
                //Retry a couple times, see what can be done
                var retrytime = 1000*meDB.connect_failures;
                console.log("Retrying connection in "+(retrytime/1000).toString()+" seconds");
                setTimeout(function() { meDB.connectServer(url); },retrytime);
            }
        }
        
        //If the connection is closed, call the function defined above
        meDB.connection.onclose = function() {
            meDB.connect_connected = false;
            meDB.connection.onerror();
        }
        
        //And now, what happens after the connection is established
        meDB.connection.onopen = function() {
            console.log("Server connection established");
            meDB.connect_connected = true; //Set the connection-established marker
            meDB.connect_failures=0;       //Reset the connection-error counter
            
            //Send the server a basic introductory message
            meDB.sendHRUD();
            
            //Now that the connection with server is established, do all necessary
            //  function bindings which send data to server. Only do the function bindings once,
            //  since we don't need these functions repeating
            if (!meDB.connect_hadconnect) {
                meDB.connect_hadconnect=true;
                
                //On window resize, send window resize event
                var resize_timeout = null;
                $(window).resize(function() {
                    clearTimeout(resize_timeout);
                    resize_timeout = setTimeout(function() {
                        meDB.sendWindowSize();
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
                        meDB.send({"k":key},
                                "Key ("+e.which.toString()+")")
                    }
                    
                    //Next, see if there is a binding associated with the key
                    var keybind = meDB.getKeyBind(key);
                    
                    if (keybind) {
                        //A keybinding exists, so act upon it
                        if (keybind.preventDefault==true) e.preventDefault();
                        if (keybind.func) keybind.func();
                    }
                });
            }
        }
        
        //Handling server-side messages - this needs to be done once for each connection
        meDB.connection.onmessage = function(e) {
            /*
                The message protocol is actually pretty simple:
                The websocket sends an object in json. This object
                is what is passed to the setopt function for decoding
            */
            meDB.setopt(JSON.parse(e.data));
        }
    
    },
    //The following functions send relevant pieces of information to the server
    send: function(data,logmsg) {
        if (meDB.connect_connected) {
            console.log('<- '+ logmsg);
            meDB.connection.send(JSON.stringify(data));
        } else {
            console.error('<- '+ logmsg+" !! FAILED, not connected");
        }
    },
    //Send a chrud message. The format is defined before the "setopt" function
    sendHRUD: function() {        
        meDB.send({
            h: [window.location.href,window.document.referrer],
            r: $(window).width().toString()+'x'+$(window).height().toString(),
            u: navigator.userAgent,
            d: window.screen.width.toString()+'x'+window.screen.height.toString()
                +'x'+window.screen.pixelDepth.toString()+'|'+Date()
        },"HRUD");
    },
    sendWindowSize: function(text) {
        if (!text) text="Window Size";
        meDB.send({'r': $(window).width().toString()+'x'+$(window).height().toString()},
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
    
    setKeyBind: function(key,preventdefault,funct,del) {
        var keyobj = meDB.getKeyBind(key);
        
        if (!keyobj) {
            console.log("Keybind <=: new("+key.n+")");
            //Check to see if there is an array declared at the key
            if (!meDB.keyboard[key.n]) {
                meDB.keyboard[key.n]=[];
            }
            //Add keybinding to the array
            meDB.keyboard[key.n].push({ c: key.c, s: key.s, a: key.a,
                        preventDefault: preventdefault, func: funct});
        } else {
            if (del) {
                console.log("Keybind <=: delete("+key.n+")");
                
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
                console.log("Keybind <=: update("+key.n+")");
                //Just update the links
                keyobj.preventDefault = preventdefault;
                keyobj.func = funct;
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
            
            e: Editor options (id of document being referred to, and what happened)
            a: User drag-dropped file, and contents if not localhost
            
        Recieve:
            i: set session ID
            t: set title of window
            k: map/change key mapping
            ks: Toggle sending of keystrokes on or off
            r: resize window
            h: send hrud package
            id: send session ID
            
            c: Close view (given id of view)
            e: Editor options (given id of document to act upon)
            n: Add new view
    */
    setopt: function(opt) {        
        for (var option in opt) {
            switch (option) {
                
                case "k":
                    var key = opt[option];
                    //Keybindings come in arrays
                    for (k in key) {
                        meDB.setKeyBind(key[k].k,key[k].p,null,key[k].d);
                    }
                    break;
                case "ks":
                    console.log("Send Keystrokes <=: "+opt[option]);
                    meDB.keylogger = opt[option];
                    break;
                case "t":
                    console.log('Window Title <=: "'+opt[option]+'"');
                    document.title = opt[option];
                    break;
                case "i":
                    console.log('Session ID <=: "'+opt[option]+'"');
                    meDB.sessionID = opt[option];
                    break;
                case "id":
                    console.log('Session ID <- request send');
                    meDB.send({i:meDB.sessionID},"Session ID");
                    break;
                case "h":
                    meDB.sendHRUD();
                    break;
                case "r":
                    console.log('Window Size <=: "'+opt[option]+'"');
                    window.resizeTo(opt[option].w,opt[option].h);
                    break;
                default:
                    console.error("Server command not recognized",10);
            }
        }
        
        
    },
    //An error of this magnitude is cause for concern - the editor 
    criticalError: function(reason) {
        //TODO: If there are theme functions for display of errors, use them
        alert("CRITICAL ERROR:\n"+reason);
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

meDB.connectServer("wss://10.136.84.76:8000/q");
