// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCsUb2mCviJEKisMI9oFe7pqyigKL2dzkY",
  authDomain: "real-estate-project-445516.firebaseapp.com",
  projectId: "real-estate-project-445516",
  storageBucket: "real-estate-project-445516.firebasestorage.app",
  messagingSenderId: "933297378726",
  appId: "1:933297378726:web:234baffe9ab382045a2b67",
  measurementId: "G-EP2L8DXXLJ",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Cloud Firestore and get a reference to the service
const db = getFirestore(app);

export { db };
