/*setInterval(window.onload = function refreshList(){

    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }


    xmlhttp.onreadystatechange=function() {
        if (xmlhttp.readyState==4 && xmlhttp.status==200) {

            var page = (JSON.parse(xmlhttp.responseText));
            document.getElementById("userList").innerHTML = page.page
        }
    }

    xmlhttp.open("GET","/refreshUserList", true);
    xmlhttp.send();
},1000)*/

function goToBottom(){
	var element = document.getElementById("chatlogs");
	element.scrollTop = element.scrollHeight;
}

setInterval(window.onload = function refreshChat(){

    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }


    xmlhttp.onreadystatechange=function() {
        if (xmlhttp.readyState==4 && xmlhttp.status==200) {

            var page = (JSON.parse(xmlhttp.responseText));    
	    console.log(page.newMessage);
            if (page.newMessage == 'True') {
		    
		    var el = document.createElement("div")
		    var att = document.createAttribute("class");
		    att.value = "chat self";
		    el.setAttributeNode(att);
                    
		    
            	    var oldChat = document.getElementById("chatlogs");
		    oldChat.append(el)

		    
            }
            
        }
    }


    xmlhttp.open("GET","/refreshChat", true);
    xmlhttp.send();
},1000)
