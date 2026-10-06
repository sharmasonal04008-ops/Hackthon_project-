print hello world in C
#include<stdio.h>
int main()
 {
    printf("hello world");
    return 0;
 }


// variable
#include<stdio.h>
int main()
{
int number = 24,45,43,21,79;
char star = '*';
int age = 20;
float pi = 3.14;
return 0;
}
Using scanf for taking input 

 #include<stdio.h>
int main()
{
    int age;
    printf("enter age");
    scanf("%d",&age);
    printf("age is : %d" ,age);
    return 0;
}

addition of two numbers takin input from user
 #include<stdio.h>
 int main()
 {
    int a,b,sum;
    printf("enter the number a:");
    scanf("%d",&a);
    printf("enter the number b:");
    scanf("%d",&b);
    sum = a+b;
    printf("sum of a and b:%d",sum);
    return 0;
 }

square of two numbers taking input from user

#include <stdio.h>
int main()
{
    int a,square;
    printf("enter the number a:");
    scanf("%d",&a);
    square = a * a;
    printf("square:%d",square);
    return 0;
}
calculate radius of circle 
#include <stdio.h>
int main()
{
    int a;
    float area;
    printf("enter the radius:");
    scanf("%d",&a);
    area = 3.14*a*a;
    printf("area of circle:%.2f",area);
    return 0;
}


    
    
    
