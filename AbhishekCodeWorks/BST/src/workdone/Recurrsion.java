package workdone;
public class Recurrsion{
    public static void main(String[] args) {
        print(1);
    }

    static void print(int n ){
        if(n == 5){
            System.out.print(n +" ");
            return;
        }
       System.out.print(n + " " );
       print(n+1);
    }
    
}


