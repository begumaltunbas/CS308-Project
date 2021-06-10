import React from 'react';
import {FormGroup, Input} from 'reactstrap';
import { useEffect } from "react";
import {useState} from "react";
import Cookies from 'js-cookie'
import { Grid, Paper } from '@material-ui/core';
import { useLocation } from "react-router-dom";
import { Document, Page } from 'react-pdf/dist/esm/entry.webpack';
import { pdfjs } from 'react-pdf';
import pdfjsWorker from "pdfjs-dist/build/pdf.worker.entry";

export const OrderDetail = ({product}) => {
 
  pdfjs.GlobalWorkerOptions.workerSrc = 'pdf.worker.min.js';

  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [invoice, setInvoice] = useState(1);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  const location = useLocation();
  const [productlist, setProductList] = useState([]);

  useEffect(() => {
    getOrdetDetails();
    pdfjs.GlobalWorkerOptions.workerSrc = 'pdf.worker.min.js';

  }, []);

  const getOrdetDetails = async () => {
        
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

    const response = await fetch('http://localhost:5000/pmview', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        user: username,
        token: token_id,
      },
      body: JSON.stringify({
        'cart_id': location.state.product.cart_id,
       
      })

    })
     let json = await response.json();

    console.log("JSOOOOOONN", json)
    
    setProductList(json);
    setInvoice(json.invoice)
    console.log(invoice)
    console.log("listimiz bu",productlist )
  }

  useEffect(() => {
    console.log(location.state.product); // result: 'some_value'
 }, [location]);

  const starStyle = {
    width: 155,
    height: 35,
    marginBottom: 20,
  };
  const str = "data:application/pdf;base64" +invoice 
  console.log("HEY",str)
  //const { cart_id,order_id,itemlist,order_status,order_time,total_amount,total_price } = product.params;
      return (
	  <div  >
        {/* <Image style={{marginLeft:20 , width:65, height: 70, marginTop:10,marginBottom: 0 }}
        source={{
          uri: 'http://cdn.onlinewebfonts.com/svg/img_330183.png'
        }}/> */}
         <text style={{ marginTop: 25, paddingLeft:10,fontSize: 25, marginRight: 30,fontWeight: 'bold', color: '#BFA38F'  }}>   Order Info </text>
         <br></br>
         <text style={{ marginTop: 25, paddingLeft:10,fontSize: 25, marginRight: 30,fontWeight: 'bold' }}>   Date of purchase: </text>
         <text style={{ marginTop: 25, paddingLeft:10,fontSize: 25, marginRight: 30 }}> {productlist.date_of_purchase} </text>
         <br></br>
         <text style={{ marginTop: 25, paddingLeft:10,fontSize: 25, marginRight: 30,fontWeight: 'bold' }}>   Address: </text>
         <text style={{ marginTop: 25, paddingLeft:10,fontSize: 25, marginRight: 30 }}> {productlist.address} </text>
         <br></br>
         <text style={{ marginTop: 25, paddingLeft:10,fontSize: 25, marginRight: 30,fontWeight: 'bold' }}>   Phone: </text>
         <text style={{ marginTop: 25, paddingLeft:10,fontSize: 25, marginRight: 30 }}>  {productlist.phone} </text>
   
    
     
      	<div
			style={{
			//borderBottomColor: '#BFA38F',
				borderColor: '#000000bf',
				borderBottomWidth: 5,
				borderEndWidth: 1000,
				}}
		/>
      {console.log(invoice)}
      
      <Document
      options = {{cMapUrl: `//cdn.jsdelivr.net/npm/pdfjs-dist@2.8.335/cmaps/`, cMapPacked: true}}

      file={`data:application/pdf;base64,${invoice}`}
        onLoadSuccess={onDocumentLoadSuccess}
        >
          <Page pageNumber={pageNumber} />
        </Document>
        <p>Page {pageNumber} of {numPages}</p>

         {/* <Button
              title="Show Invoice"
              onPress={() => navigation.navigate('Invoice', {
                cart_id:cart_id,
              })} //navigate
            /> */}
        

    </div>
  );
};

export default OrderDetail;
