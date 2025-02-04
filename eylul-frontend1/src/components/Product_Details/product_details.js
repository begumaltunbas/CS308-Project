import React from 'react';
import {FormGroup, Input} from 'reactstrap';
import "./product_details.css";
import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import {useState} from "react";
import Cookies from 'js-cookie'
import Comments from './comments/comments';
import { Grid, Paper } from '@material-ui/core';
import { useHistory } from "react-router-dom"; 
import { IconButton} from '@material-ui/core';


 const Product_Detail = (product) => {
  const history = useHistory();
  let userType =  Cookies.get('userType');
      const location = useLocation();
      const [comments, setComments] = useState([]);
      const [stock, setStock] = React.useState(null);
      const [discount, setDiscount] = React.useState(null);
      const giveDiscount = async () => {
        
        let token_id = 0;
        let username = 0;
    
        try {
          token_id = await Cookies.get('token');
        } catch(e) {
          console.log(e);
        }
    
        try {
          username = await Cookies.get('userName'); 
        } catch(e) {
          console.log(e);
        }
    
        const response = await fetch('http://localhost:5000/discount', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            user: username,
            token: token_id,
          },
          body: JSON.stringify({
            'product_name': location.state.product.name,
            'discount':discount
           
          })
    
        })
        let json = await response.json();

        console.log("JSOOOOOONN", json)

      }
      const discountPrice = (val) => {
       setDiscount(val)
    }

    const increaseStock = async () => {
      var mystock = parseInt(stock)
      let token_id = 0;
      let username = 0;
  
      try {
        token_id = await Cookies.get('token');
      } catch(e) {
        console.log(e);
      }
  
      try {
        username = await Cookies.get('userName'); 
      } catch(e) {
        console.log(e);
      }
  
      const response = await fetch('http://localhost:5000/stock', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          user: username,
          token: token_id,
        },
        body: JSON.stringify({
          'product_name': location.state.product.name,
          'increase':mystock
         
        })
  
      })
      let json = await response.json();

      console.log("JSOOOOOONN", json)

    }

    const newStock = (val) => {
      setStock(val)
  }

  const decreaseStock = async () => {
    var mystock = parseInt(stock)
    let token_id = 0;
    let username = 0;

    try {
      token_id = await Cookies.get('token');
    } catch(e) {
      console.log(e);
    }

    try {
      username = await Cookies.get('userName'); 
    } catch(e) {
      console.log(e);
    }

    const response = await fetch('http://localhost:5000/stock', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        user: username,
        token: token_id,
      },
      body: JSON.stringify({
        'product_name': location.state.product.name,
        'decrease':mystock
       
      })

    })
    let json = await response.json();

    console.log("JSOOOOOONN", json)

  }


  const removeProduct = async () => {
    
    let token_id = 0;
    let username = 0;

    try {
      token_id = await Cookies.get('token');
    } catch(e) {
      console.log(e);
    }

    try {
      username = await Cookies.get('userName'); 
    } catch(e) {
      console.log(e);
    }

    const response = await fetch('http://localhost:5000/stock', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        user: username,
        token: token_id,
      },
      body: JSON.stringify({
        'product_name': location.state.product.name,
        'remove':true
       
      })

    })
    let json = await response.json();

    console.log("JSOOOOOONN", json)
    history.push("/home")
  }


      const HandleAddtoCart = async (name) => {

        let token_id = 0;
        let username = 0;
    
        try {
          token_id = await Cookies.get('token');
          // setToken(token_id);
        } catch (e) {
          console.log(e);
        }
    
        try {
          // await AsyncStorage.setItem('userToken', userToken);
          username = await Cookies.get('userName');
          // setUsername(username);
        } catch (e) {
          console.log(e);
        }
    
        // console.log("home screen- TOKEN id that we sent to backend::!!!", token_id);
        // console.log("home screen- USERNAME that we sent to backend::!!!", username);
    
    
        const response2 = await fetch('http://localhost:5000/basket', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            user: username,
            token: token_id,
          },
          body: JSON.stringify({
            //category_name:'Coffee Machines'
            product_name: name,
            quantity: 1
    
          })
    
        })
    
        // console.log("username2 geldi mi?????", username); //GELMEDİ KONTROL ET!!!!!!!!!!!!!!!!!
        let json = await response2.json();
    
    
        if(json.status_code === 200){
          alert("Your cart is updated")
     
        }
        else{
          alert("Try again!")
        }
        console.log("mesajımız: ", json.message)
        console.log("code: ", json.status_code)
        //setBasket(json.category_elements);  
      }

      const getComments= async() =>{
        const response = await fetch('http://localhost:5000/getcomment',{
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept:"application/json",
            },
                body: JSON.stringify({
                product_name: location.state.product.name
                })
            })
            let json=await response.json();
            setComments(json.comments);
            console.log("comments", comments)
        }

    useEffect(() => {
        getComments();
    }, []) 
      useEffect(() => {
        console.log(location.state.product); // result: 'some_value'
      }, [location]);

      return (<>
	  <div className="card">
  <div className="photo">
    <img src={location.state.product.image_path} />
  </div>
  <div className="description">
    <h2 className="h2_b">{location.state.product.name}</h2>
    <h3 className="h3_b">Rating: {location.state.product.rating}</h3>
    
    {location.state.product.discount === 0 &&  <h1 className="h1_b">${location.state.product.price}</h1>}
    {location.state.product.discount !== 0 && <h1 className="h6_b">${location.state.product.price}</h1>}
    {location.state.product.discount !== 0 && <h1 className="h7_b">${location.state.product.price-(location.state.product.price*location.state.product.discount/100)}</h1>}
    <p className="p_b">{location.state.product.model}.</p>
    <h4 className="h4_b">Item in Stock: {location.state.product.stock}</h4>
    <button onClick={() => { { product.stock !== 0 ? HandleAddtoCart(location.state.product.name,1): (alert("Item is out of stock!")) }}} className="button_b">Add to Cart</button>
    
    {userType==="product manager" &&<button className="button_b" onClick={() => removeProduct()}> Remove Product </button>}
    
    {userType==="sales manager" &&
    <div >
            <input 
                        placeholder="Enter Discount Percentage"
                        placeholderTextColor='#000000bf'
                            
                        onChange={(val) =>discountPrice(val.target.value)}          
            />
        </div>}
    {userType==="sales manager" &&
    <button style={{marginLeft:20}}
                title="Update inff"
                onClick={() => {
                    if (discount !==false ) {
                        giveDiscount();
                        alert('Discount is given')
                      }
                    else{ }
                    
                }
                }
                > Set Discount </button>}

{userType==="product manager" &&
    <div >
            <input 
                        placeholder="Quantity"
                        placeholderTextColor='#000000bf'
                            
                        onChange={(val) =>newStock(val.target.value)}          
            />
        </div>}
    {userType==="product manager" &&
    <button style={{marginLeft:20}}
                title="Update inff"
                onClick={() => {
                    if (discount !==false ) {
                      increaseStock();
                        alert('Discount is given')
                      }
                    else{ }
                    
                }
                }
                > Increase Stock </button>}


{userType==="product manager" &&
    <div >
            <input 
                        placeholder="Quantity"
                        placeholderTextColor='#000000bf'
                            
                        onChange={(val) =>newStock(val.target.value)}          
            />
        </div>}
    {userType==="product manager" &&
    <button style={{marginLeft:20}}
                title="Update inff"
                onClick={() => {
                    if (discount !==false ) {
                      decreaseStock();
                        alert('Discount is given')
                      }
                    else{ }
                    
                }
                }
                > Decrease Stock </button>}



  </div>
  <div className="comments">
    <h3 className="h3_b">Comments</h3>
    <div className="single-comment">
    {/*<h4 style={{marginTop: "5px"}} className="h4_b">Deniz Atalay</h4>
    <h4 style={{marginLeft: "3px"}} className="p_b">{comments.text}</h4>*/}
    

    <Grid container spacing={5}>
      {comments.map((comm) => (
          <Grid item key={location.state.product.product_id} xs={12} sm={6} md={10} lg={12} >
          <Comments item={comm} getComments={getComments} />
        </Grid>
        ))}
    </Grid>

    </div>
    <div classNAme='pdf-container'>

    </div>
    <div>
    {/*<FormGroup>
        <Input style={{float: "center"}} type="textarea" placeholder="You can comment here..."
        style={{resize: "none", width: "90%"}} name="text" id="exampleText" />
      </FormGroup>
    <button style={{marginTop: "7px" , position: "relative"}} className="button_b">Comment!</button>*/}
    </div>
  </div>
</div>

</>

  );
};

export default Product_Detail;