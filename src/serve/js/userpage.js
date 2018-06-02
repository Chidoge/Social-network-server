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

            try {
                var page = (JSON.parse(xmlhttp.responseText));
                var oldChat = document.getElementById("chatlogs");
                console.log('Message' + page.newChat);

                messages = page.newChat.split(";");
                console.log('After split : ' + messages[0]);
                for (var i =0;i<messages.length -1 ;i++){

                    console.log('Message after split: ' + messages[i]);
                    var el = document.createElement("div");
                    var att = document.createAttribute("class");

                    if (messages[i][0] == 's') {

                        att.value = "chat self";
                                
                    }
                    else {
                        att.value = "chat friend";
                    }

                    el.setAttributeNode(att);
                    console.log("Clean message " + messages[i].substring(1));
                    el.innerHTML = String(messages[i].substring(1));
                    console.log('Inner html' + el.innerHTML);
                    oldChat.append(el);
                    var element = document.getElementById("chatlogs");
                    element.scrollTop = element.scrollHeight;

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
