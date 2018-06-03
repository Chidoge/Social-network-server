function init() {

    getList();

    var element = document.getElementById("chatlogs");
    if (element != null) {
        element.scrollTop = element.scrollHeight;
    }

}

/* Gets the user list on page start up */
function getList() {

    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }

    xmlhttp.onreadystatechange=function() {

        if (xmlhttp.readyState==4 && xmlhttp.status==200) {
            var page = (JSON.parse(xmlhttp.responseText));
            if (page.page != undefined){

                document.getElementById("userList").innerHTML = page.page;
            }
        }
    }

    xmlhttp.open("GET","/refreshUserList", true);
    xmlhttp.send();
}

/* Continues to refresh the list */
setInterval(window.onload = function refreshList(){

    if (window.XMLHttpRequest) {
        xmlhttpReq = new XMLHttpRequest();
    }


    xmlhttpReq.onreadystatechange=function() {
        if (xmlhttpReq.readyState==4 && xmlhttpReq.status==200) {
            var page = (JSON.parse(xmlhttpReq.responseText));
            if (page.page != undefined){
                document.getElementById("userList").innerHTML = page.page;
            }
        }
    }

    xmlhttpReq.open("GET","/refreshUserList", true);
    xmlhttpReq.send();

},5000);


/* Calls the send message function in python */
function sendMessage() {

    var text = document.getElementById("textForm");
    var message = text.elements['message'].value;
    console.log(message);

    document.getElementById("textForm").reset();
    xmlhttp.open("POST","/sendMessage?message="+message, true);
    xmlhttp.send();
}


function showMessageReceipt() {

    var snackBar = document.getElementById('messageReceipt');

    snackBar.className = "show";

    setTimeout(function() {
        snackBar.className = snackBar.className.replace("show","");
    },1500);
}

function sendFile(){

    var file = document.querySelector('#fileForm').files[0];
    fileData = getBase64(file);
}


function getBase64(file) {

    var reader = new FileReader();
    reader.readAsDataURL(file);

    reader.onload = function () {


        var fileData = reader.result;
        var mimetype = reader.result;
        console.log(reader.result);
        var index = fileData.indexOf(",");
        var indexColon = mimetype.indexOf(":");
        var indexSemi = mimetype.indexOf(";");

        fileData = fileData.substring(index + 1);
        mimetype = mimetype.substring(indexColon+1,indexSemi);

        xmlhttp.open("POST","/sendFile",true);
        xmlhttp.setRequestHeader("Content-Type", "application/json");
        var data = JSON.stringify({'fileData' : fileData , 'mimetype' : mimetype});
        xmlhttp.send(data);
   };

}

/* Continues to refresh chat box */
setInterval(window.onload = function refreshChat(){

    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }


    xmlhttp.onreadystatechange=function() {

        if (xmlhttp.readyState==4 && xmlhttp.status==200) {

            try {
                var page = (JSON.parse(xmlhttp.responseText));
                var oldChat = document.getElementById("chatlogs");
                var messageSent = false;
                messages = page.newChat.split(";");
                for (var i =0;i<messages.length -1 ;i++){

                    var el = document.createElement("div");
                    var att = document.createAttribute("class");

                    if (messages[i][0] == 's') {

                        att.value = "chat self";
                        messageSent = true;
                                
                    }
                    else {
                        att.value = "chat friend";
                    }

                    el.setAttributeNode(att);
                    el.innerHTML = String(messages[i].substring(1));
                    oldChat.append(el);
                    var element = document.getElementById("chatlogs");
                    element.scrollTop = element.scrollHeight;
                }
                        
                if (messageSent == true){
                    showMessageReceipt();
                }
            }
            
            catch (parseError){
                console.log('Caught json parseError');
                return;
            }
        }
    }

    xmlhttp.open("GET","/refreshChat", true);
    xmlhttp.send();

},1000)


setInterval(window.onload = function notify() {

    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }


    xmlhttp.onreadystatechange=function() {

        if (xmlhttp.readyState==4 && xmlhttp.status==200) {
            try {
                var notification = (JSON.parse(xmlhttp.responseText));
                if (notification.newMessage == 'True'){
                    var notiBar = document.getElementById('notiBar');
                    notiBar.innerHTML = notification.messageFrom;
                }
            }
            catch (parseError) {
                console.log('Caught json parse error');
            }
           
        }
    }
    

    xmlhttp.open("GET","/notify", true);
    xmlhttp.send();

},5000)
