-- database/schema.sql
CREATE DATABASE IF NOT EXISTS hlis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hlis;

CREATE TABLE Patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    HN VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    dob DATE,
    blood_type ENUM('A','B','AB','O') DEFAULT NULL,
    contact_phone VARCHAR(20)
);

CREATE TABLE Staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role ENUM('doctor','lab','admin') NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE Test_Type (
    test_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    unit VARCHAR(20),
    normal_min DECIMAL(10,2),
    normal_max DECIMAL(10,2),
    price DECIMAL(10,2) NOT NULL
);

CREATE TABLE Lab_Order (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending','completed','cancelled') DEFAULT 'pending',
    priority ENUM('routine','urgent') DEFAULT 'routine',
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Staff(staff_id)
);

CREATE TABLE Lab_Order_Item (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    test_id INT NOT NULL,
    item_status ENUM('pending','completed') DEFAULT 'pending',
    FOREIGN KEY (order_id) REFERENCES Lab_Order(order_id),
    FOREIGN KEY (test_id) REFERENCES Test_Type(test_id)
);

CREATE TABLE Lab_Result (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    order_item_id INT NOT NULL UNIQUE,
    value DECIMAL(10,2) NOT NULL,
    recorded_by INT NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_abnormal BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (order_item_id) REFERENCES Lab_Order_Item(order_item_id),
    FOREIGN KEY (recorded_by) REFERENCES Staff(staff_id)
);

CREATE TABLE Billing (
    billing_id INT AUTO_INCREMENT PRIMARY KEY,
    order_item_id INT NOT NULL UNIQUE,
    unit_price DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_item_id) REFERENCES Lab_Order_Item(order_item_id)
);