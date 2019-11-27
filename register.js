let addr = document.getElementById("remove-address");
let debit = document.getElementById("remove-debit");

function toggleShipAddress(){
    let staffButton = document.getElementById("staff");
    if(staffButton.checked == true){
        addr.style.display = "none";
        debit.style.display= "none";
    }
    else{
        addr.style.display = "block";
        debit.style.display = "block";
    }
    
}