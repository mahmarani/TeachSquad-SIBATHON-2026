// ---------- HOME PRODUCTS ----------
if(document.getElementById("products")){
fetch("/api/products")
.then(r=>r.json())
.then(data=>{
    let html="";
    data.forEach(p=>{
        html+=`
        <div class="card">
            <a href="/product/${p.id}">
            <img src="/static/img/${p.image}">
            </a>
            <h3>${p.name}</h3>
            <p>Rs ${p.price}</p>
            <button onclick="addToCart(${p.id})">Add to Cart</button>
        </div>`;
    });
    document.getElementById("products").innerHTML=html;
});
}

// ---------- PRODUCT DETAIL ----------
if(document.getElementById("product")){
const id=window.location.pathname.split("/").pop();

fetch("/api/product/"+id)
.then(r=>r.json())
.then(p=>{
document.getElementById("product").innerHTML=`
<h1>${p.name}</h1>
<img src="/static/img/${p.image}" style="width:250px">
<p>${p.brand}</p>
<p>Rs ${p.price}</p>
<button onclick="addToCart(${p.id})">Add to Cart</button>
`;
});
}

// ---------- ADD ----------
function addToCart(id){
fetch("/api/cart/add",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({product_id:id})
}).then(()=>alert("Added to cart"));
}

// ---------- CART ----------
if(document.getElementById("cartItems")){
fetch("/api/cart")
.then(r=>r.json())
.then(data=>{
let html=""; let total=0;
data.forEach(it=>{
total+=it.line_total;
html+=`${it.name} x ${it.qty} = Rs ${it.line_total}
<button onclick="removeItem(${it.id})">Remove</button><br>`;
});
document.getElementById("cartItems").innerHTML=html;
document.getElementById("total").innerText="Total Rs "+total;
});
}

// ---------- REMOVE ----------
function removeItem(id){
fetch("/api/cart/remove",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({product_id:id})
}).then(()=>location.reload());
}

// ---------- ORDERS ----------
if(document.getElementById("orders")){
fetch("/api/orders")
.then(r=>r.json())
.then(data=>{
let html="";
data.forEach(o=>{
html+=`<div>Order by ${o.user} — ${o.address}</div>`;
});
document.getElementById("orders").innerHTML=html;
});
}
