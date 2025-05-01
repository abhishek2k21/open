package threadwork;

public class Company {

    int n ;
    synchronized public void producer_item(int n ){
        this.n = n;
        System.out.println("Produced: " + this.n);
    }

    synchronized public int  consume_item(){
    System.out.println("Consumed: " + this.n);
    return this.n;
    }

}
