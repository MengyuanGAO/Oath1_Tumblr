# OAuth & Data Processing —— Tumblr


## Instructions

* The goal in this project is to plan what data you want to get from an API in order to create CSV files of data that's interesting to you, set up a caching system for your data so that data is cached for a reasonable amount of time when you run the program, write unit tests for your project that will help you ensure it works correctly, and ultimately write code to successfully gather and process data from a REST API that uses some form of complex authentication.


* **Step 1:** Choose API

  * [The Tumblr API](https://www.tumblr.com/docs/en/api/v2#auth) 

* **Step 2 :** Edit `SI507project5_tests.py` with unit tests for the project you plan. Don't change the name of this file. There should be at **least 1 subclass of `unittest.TestCase`**, at least **5 total test methods** (consider what you most need to test!), at least one use of the **`setUp`** and **`tearDown`** test methods.


* **Step 3 :** Edit `SI507project5_code.py` as follows:

    * Implement a caching system that ensures you will not run afoul of the rate limit of whatever API you use, and that you will not get data from the same request more than once per 12 hours, no matter how many times you run the program. 

  * Get data from this API using OAuth1 authentication 
  
  * Create `.CSV` files of data.



 
