setInterval(window.onload = function refreshList(){

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
},1000)


setInterval(window.onload = function refreshChat(){

    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }


    xmlhttp.onreadystatechange=function() {
        if (xmlhttp.readyState==4 && xmlhttp.status==200) {

            var page = (JSON.parse(xmlhttp.responseText));
            document.getElementById("chatlogs").innerHTML = page.page

            if (page.newMessage == 'True') {
            	var element = document.getElementById("chatlogs");
    			element.scrollTop = element.scrollHeight;
            }
        }
    }


    xmlhttp.open("GET","/refreshChat", true);
    xmlhttp.send();
},1000)
