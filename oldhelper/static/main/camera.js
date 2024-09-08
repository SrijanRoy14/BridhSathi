let CaptureButton,
  CaptureMultiButton,
  folder,
  lable_input,
  capturedone = false,
  number,
  startstopbutton,
  emer,pred,
  responsetext;
const buttoncontainer = document.getElementById("capturecontainer");
const cameraFeed = document.getElementById("cameraFeed");
const perpImagesContainer = document.getElementById("perpetrator-images");
const socket = new WebSocket("ws://" + window.location.host + "/ws/video/");
const mainbody=document.getElementById("mainbody");
const perpresponsecontainer=document.getElementById("perpresponsecontainer");
cameraFeed.style.display = 'none';

socket.onmessage = function (event) {
  try{
  cameraFeed.src = "data:image/jpeg;base64," + event.data;
  }
  catch{
    console.error();
  }

  try {
    const data = JSON.parse(event.data);
    console.log(event.data);
    if (String(data.action) === "DB_Latest") {
      
      removebyid("perpimage", perpImagesContainer);
      removebyid("perpresponse", perpresponsecontainer);
      removebyid("imagecaption",perpImagesContainer);

      //perpImagesContainer.removeChild(perpresponse);
      let labeldata;
      const label = String(data.label);
      if (label==="fine") 
        {labeldata="Hey I am fine now!";}
      
      else if(label==="danger") {labeldata="Hey I am in danger, need help!!!";}
      else if(label==='stolen'){labeldata="Hey some things are stolen!!";}
      else{labeldata="Hey I need you to call!";}

      

      
      const perpresponse = document.createElement("h3");
      const imagecaption = document.createElement("h4");
      const perpImg = document.createElement("img");
      perpresponse.textContent = labeldata;
      perpImg.id = "perpimage";
      perpresponse.id = "perpresponse";
      imagecaption.id="imagecaption";

      perpresponsecontainer.appendChild(perpresponse);
      if (label==='danger' || label==="stolen") 
        {
          console.log(label);
          
          var created_at=String(data.created_at);

          const link = document.createElement("a");
          link.href = String(data.location);//"https://maps.google.com/?q=" + lat + "," + long;
          link.textContent = "Location";


          const body = document.createTextNode("The image was taken at " + created_at+" " );
          imagecaption.appendChild(body);
          imagecaption.appendChild(link);

          perpImg.src = String(data.captured_image);
          perpImg.caption = "This is the last captured image";
          perpImagesContainer.appendChild(perpImg);
          perpImagesContainer.appendChild(imagecaption);
      }
    }
  } catch {
    console.error();
  }

  if (String(event.data) === "Done") {
    console.log("received!");
    capturedone = true;
    //let startstopbutton = document.getElementById("startStream");
    //addbyid("capturemultibutton", capturecontainer, CaptureMultiButton);
    startstopbutton.style.visibility = "visible";
    emer.style.visibility = "visible";
    pred.style.visibility = "visible";
    capturecontainer.removeChild(responsetext);
    addbyid("startStream", capturecontainer, startstopbutton);
    addbyid("capturemultibutton", capturecontainer, CaptureMultiButton);
    capturecontainer.appendChild(CaptureButton);
  }
};

socket.onclose = function (event) {
  console.error("WebSocket closed unexpectedly");
};

// Function to send message to start the stream
function startStream() {
  console.log("Here");
  cameraFeed.style.display = 'block';
  socket.send(JSON.stringify({ action: "start" }));
}

// Function to send message to stop the stream
function stopStream() {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ action: "stop" }));
    cameraFeed.style.display = 'none';
    console.log("Stop stream command sent");
  } else {
    console.error("WebSocket is not open. Current state: " + socket.readyState); //if the socket is closed and we are trying to send message to a closed connection
  }
}

function capturemulti() {
  folder = document.createElement("form");
  folder.id = "submitform";

  lable_input = document.createElement("input");
  lable_input.type = "text";
  lable_input.name = "message";
  lable_input.placeholder = "Enter folder name";
  lable_input.required = true;
  folder.appendChild(lable_input);

  no_img = document.createElement("input");
  no_img.type = "number";
  no_img.name = "number";
  no_img.min = "1";
  no_img.max = "100";
  no_img.required = true;
  no_img.placeholder = "Enter The number of images";
  folder.appendChild(no_img);

  const submitButton = document.createElement("button");
  submitButton.type = "submit";
  submitButton.textContent = "Submit";
  folder.appendChild(submitButton);

  folderlabel.appendChild(folder);

  folder.addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the default form submission
    const name = event.target.message.value; // Get the value from the input
    number = event.target.number.value; // Get the value from the input

    //console.log(no_img);
    //console.log(event.target.message.value);
    //console.log("Message submitted:", number, name);

    socket.send(
      JSON.stringify({
        action: "capturemulti",
        label: name,
        number: number,
      })
    );
    if (capturedone) {
      console.log("affirmation recieved!");
    }

    responsetext = document.createTextNode(
      "Please wait collecting your pictures"
    );
    capturecontainer.appendChild(responsetext);
    //folderlabel.removeChild(folder);
    startstopbutton = document.getElementById("startStream");
    emer = document.getElementById("emer");
    pred = document.getElementById("pred");
    startstopbutton.style.visibility = "hidden";
    emer.style.visibility = "hidden";
    pred.style.visibility = "hidden";
    //removebyid("startStream", capturecontainer);
    removebyid("submitform", folderlabel);
  });
}

function addcapturebutton() {
  //function to dynamically append the "capture button" to the div-- yet to add the func
  CaptureButton = document.createElement("button");
  CaptureMultiButton = document.createElement("button");

  CaptureButton.id = "capturebutton";
  CaptureMultiButton.id = "capturemultibutton";

  CaptureButton.textContent = "Capture";
  CaptureMultiButton.textContent = "Capture Multi";

  CaptureButton.addEventListener("click", () => {
    console.log("Here in the new button i was");
    socket.send(JSON.stringify({ action: "capture" }));
  });

  CaptureMultiButton.addEventListener("click", () => {
    console.log("I am here in the multi capture button");
    capturecontainer.removeChild(CaptureButton);
    capturemulti();
    removebyid("capturemultibutton", capturecontainer);

    console.log("I am here after performing capture multi!");
    //socket.send(JSON.stringify({'action': 'capture'}));
  });

  //capturecontainer.appendChild(CaptureButton);

  addbyid("capturebutton", capturecontainer, CaptureButton);
  addbyid("capturemultibutton", capturecontainer, CaptureMultiButton);

  //capturecontainer.appendChild(CaptureMultiButton);
}

function removebyid(elemID, divlabel) {
  const elemexists = document.getElementById(elemID);

  if (elemexists && divlabel.contains(elemexists)) {
    divlabel.removeChild(elemexists);
    console.log(`Element with ID "${elemID}" removed.`);
  } else {
    console.log(`No Element with ID "${elemID}" found in formLabel.`);
  }
}

function addbyid(elemID, divlabel, varname) {
  const elemexists = document.getElementById(elemID);

  if (elemexists && divlabel.contains(elemexists)) {
    console.log(`Element found with ID "${elemID}" not added.`);
  } else {
    divlabel.appendChild(varname);
    console.log(`No Element with ID "${elemID}" found in "${divlabel}" added.`);
  }
}

let startcam = true;
// Event listener for "Start Stream" button
document.getElementById("startStream").addEventListener("click", function (e) {
  if (startcam) {
    //toggle both button functionality and text on the basis of last action performed
    e.preventDefault(); // Prevent default button behavior
    document.getElementById("startStream").textContent = "Close Stream";
    startStream(); // Start the stream
    addcapturebutton();
  } else {
    e.preventDefault();
    document.getElementById("startStream").textContent = "Start Stream";
    stopStream();

    removebyid("capturebutton", capturecontainer);
    removebyid("capturemultibutton", capturecontainer);
    removebyid("submitform", folderlabel);
  }
  startcam = !startcam; //toggle state
});
