import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, SafeAreaView, ScrollView, TextInput,FlatList, Image } from 'react-native';
import AsyncStorage from '@react-native-community/async-storage';
import { Button } from './Products/Button';
import PropTypes from 'prop-types';
import { useIsFocused } from "@react-navigation/native";
import ModalDropdown from 'react-native-modal-dropdown';
import {Dimensions} from "react-native";
var {height, width} = Dimensions.get('window');

const HomeScreen = ({ navigation }) => {

  const [productlist, setProductList] = useState([]);
  const [choice, setChoice] = useState();
  const isFocused = useIsFocused();

  const [lowest_price_FilterNumber, lowest_price_setFilterNumber] = useState();
  const [lowest_rating_FilterNumber, lowest_rating_setFilterNumber] = useState();
  const [highest_price_FilterNumber, highest_price_setFilterNumber] = useState();
  const [highest_rating_FilterNumber, highest_rating_setFilterNumber] = useState();




  useEffect(() => {
    getProducts();
  }, [isFocused]);

  // useEffect(() => {
  //   filterProducts();
  // }, [isFocused]);



  const getProducts = async () => {

    const response = await fetch('http://localhost:5000/products', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        "lowest_price": lowest_price_FilterNumber,
        "highest_price": highest_price_FilterNumber,
        "lowest_rating": lowest_rating_FilterNumber,
        "highest_rating": highest_rating_FilterNumber
      })

    })
    let json = await response.json();
    setProductList(json.category_elements);
  }


  const addToBasket = async (itemname) => {

    let token_id = 0;
    let username = 0;

    try {
      token_id = await AsyncStorage.getItem('token');
      // setToken(token_id);
    } catch (e) {
      console.log(e);
    }

    try {
      // await AsyncStorage.setItem('userToken', userToken);
      username = await AsyncStorage.getItem('userName');
      // setUsername(username);
    } catch (e) {
      console.log(e);
    }

    console.log("home screen- TOKEN id that we sent to backend::!!!", token_id);
    console.log("home screen- USERNAME that we sent to backend::!!!", username);


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
        product_name: itemname,
        quantity: 1

      })

    })

    console.log("username2 geldi mi?????", username); //GELMEDİ KONTROL ET!!!!!!!!!!!!!!!!!
    let json = await response2.json();
    //console.log("mesajımız: ", json.message)
    //console.log("code: ", json.status_code)
    //setBasket(json.category_elements);  
  }



  const SortProducts = async (option,sort) => {
    console.log("sorrtt hereee", option,sort)
    const response = await fetch('http://localhost:5000/orderBy', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        'criteria': option ,
        'orderType': sort,
      })

    })
    let json = await response.json();
    console.log("sorrtt hereee", json)
    setProductList(json.product);
  }



  const renderItem = ({ item }) => {
    //console.log("start4",item.name);
    return (

      <View style={{ flexDirection: 'row', marginVertical: 25, paddingHorizontal: 10 }}>
        <Image style={styles.image}
          source={{
            uri: item.image_path
          }} />
        <View>
          <Text style={{ width: 260, fontSize: 18, fontWeight: 'bold' }}>{item.name} </Text>

          <Text style={{ fontSize: 15 }}> Model: {item.model}</Text>
          {/* <Text style={{fontSize:18}}> Rating: {item.rating }</Text> */}
          <Text > </Text>
          <Text style={{ fontSize: 20 }}> ${item.price} </Text>
          <Text style={{ fontSize: 18 }}> Rating: {item.rating} </Text>
          <View style={styles.together}>
            <Button
              title="Add to Cart"
              onPress={() => { { item.stock !== 0 ? (addToBasket(item.name)) : (alert("Item is out of stock!")) } }}

            />
            <Button
              title="View Details"
              onPress={() => navigation.navigate('ProductDetails', {
                itemImage: item.image_path,
                itemName: item.name,
                itemModel: item.model,
                itemPrice: item.price,
                itemRating: item.rating,
                itemStock: item.stock,
              })} //navigate
            />
          </View>

        </View>
        <View>

        </View>
      </View>

    )

  };


  return (
   
    <ScrollView style={{ flex: 1 }}>
       {/* <ModalDropdown onSelect={{choice}} textStyle={{fontSize:18, color:'white'}} style={{ backgroundColor: '#000000bf',
    borderRadius: 10,
    paddingHorizontal:13,
    paddingVertical: 12,
    marginTop:20}}
    options={['Price Lowest-Highest', 'Price Highest-Lowest','Rating Highest-Lowest' , 'Rating Lowest-Highest']}>
       
        </ModalDropdown> */}


<View>

<View style={styles.action}>

  <TextInput
    fontSize={12}
    placeholder="Lowest Price"
    placeholderTextColor='#000000bf'
    style={styles.textInput}
    onChangeText={(val) => lowest_price_setFilterNumber(val)}
  />

  <TextInput
    fontSize={12}
    placeholder="Highest Price"
    placeholderTextColor='#000000bf'
    style={styles.textInput}
    onChangeText={(val) => highest_price_setFilterNumber(val)}
  />

  <TextInput
    fontSize={12}
    placeholder="Lowest Rating"
    placeholderTextColor='#000000bf'
    style={styles.textInput}
    onChangeText={(val) => lowest_rating_setFilterNumber(val)}
  />

  <TextInput
    fontSize={12}
    placeholder="Highest Rating"
    placeholderTextColor='#000000bf'
    style={styles.textInput}
    onChangeText={(val) => highest_rating_setFilterNumber(val)}
  />

</View>

<Button
  title="Filter"
  onPress={() => { getProducts() }}
/>

</View>
 
        <View style={{ flexDirection: 'row', marginVertical: 25, paddingHorizontal: 10 }}>
             <TouchableOpacity
              onPress={() => { SortProducts('price','ASC') }}>
             <Text style={{marginHorizontal:20 ,width: 90,fontWeight:'600', color:'#BFA38F'}} >Price Lowest-Highest</Text>
             </TouchableOpacity>
            <TouchableOpacity 
              onPress={() => { SortProducts('price','DESC') }}>
             <Text style={{width: 90, fontWeight:'600',color:'#BFA38F'}} >Price Highest-Lowest</Text>
             </TouchableOpacity>
             
             <TouchableOpacity 
              onPress={() => { SortProducts('rating','DESC') }}>
             <Text style={{ width: 100, fontWeight:'600',color:'#BFA38F'}}>Rating Highest-Lowest</Text>
             </TouchableOpacity>
             
             <TouchableOpacity 
              onPress={() => { SortProducts('rating','ASC') }}>
             <Text style={{width: 100, fontWeight:'600',color:'#BFA38F'}}>Rating Lowest-Highest</Text>
             </TouchableOpacity>
        </View>
        
      
      <FlatList style={{ flex: 1 }}
        data={productlist}
        renderItem={renderItem}
        keyExtractor={(item) => item.product_id.toString()}
      />

    </ScrollView>
  );
};

export default HomeScreen;


const styles = StyleSheet.create({
  container: {
    shadowColor: '#cdcdcd',
    shadowOffset: { width: 5, height: 5 },
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 5,
    marginBottom: 30,
  },
  container2: {
    justifyContent: "center",
    paddingHorizontal: 10
  },
  image: { width: 140, height: 200, marginBottom: 10 },
  rowContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  title: { fontSize: 19, fontWeight: 'bold' },
  description: { color: '#b1b1b1', marginBottom: 10 },
  price: {
    color: '#7de3bb',
    fontSize: 18,
    fontWeight: 'bold',
  },
  notInStock: { textAlign: 'center' },

  together: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  

  },
  textInput: {
    flex: 1,
    marginTop: Platform.OS === 'ios' ? 0 : -12,
    paddingLeft: 10,
    color: '#05375a',
  },
  action: {
    flexDirection: 'row',
    marginTop: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f2f2f2',
    paddingBottom: 5
},

button: {
  flexDirection: 'column',
  alignItems: "center",
  backgroundColor: "#DDDDDD",
  padding: 10,
  justifyContent: 'space-between',
},

button3: {
backgroundColor: '#000000bf',
borderRadius: 30,
alignItems: 'center',
justifyContent: 'space-around',
width: width/5,
height: height / 20,
flexDirection: 'row',

},

});