function init() {

    getList();

    var element = document.getElementById("chatlogs");
    if (element != null) {
        element.scrollTop = element.scrollHeight;
    }

}

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



setInterval(window.onload = function refreshList(){

    if (window.XMLHttpRequest) {
        xmlhttpReq = new XMLHttpRequest();
    }


    xmlhttpReq.onreadystatechange=function() {
        console.log('List refresh called');
        if (xmlhttpReq.readyState==4 && xmlhttpReq.status==200) {
            var page = (JSON.parse(xmlhttpReq.responseText));
            if (page.page != undefined){
                console.log('List refreshed');
                document.getElementById("userList").innerHTML = page.page;
            }
        }
    }

    xmlhttpReq.open("GET","/refreshUserList", true);
    xmlhttpReq.send();

},5000);


function sendMessage() {

    var text = document.getElementById("textForm");
    var message = text.elements['message'].value;
    console.log(message);

    document.getElementById("textForm").reset();
    xmlhttp.open("POST","/sendMessage?message="+message, true);
    xmlhttp.send();
}


setInterval(window.onload = function refreshChat(){

    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }


    xmlhttp.onreadystatechange=function() {

        if (xmlhttp.readyState==4 && xmlhttp.status==200) {

            var page = (JSON.parse(xmlhttp.responseText));
            var oldChat = document.getElementById("chatlogs");

            if (page.newMessage == 'True') {
                messages = page.newChat.split(";");

                for (var i =0;i<messages.length;i++){
                    console.log(messages[i]);
                    var el = document.createElement("div");
                    var att = document.createAttribute("class");

                    if (page.sender== 'self') {

                        att.value = "chat self";
                        
                    }
                    else {
                        att.value = "chat friend";
                    }

                    console.log("Chat refreshed");
                    el.setAttributeNode(att);
                    el.innerHTML = messages[i];
                    oldChat.append(el);
                }
                
                var element = document.getElementById("chatlogs");
                element.scrollTop = element.scrollHeight;

                xmlhttp.open("POST","/setMessageDisplayed",true);
                xmlhttp.send();
            }
            

        }
    }

    xmlhttp.open("GET","/refreshChat", true);
    xmlhttp.send();

},1000)
