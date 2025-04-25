import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.manager import DatabaseManager
from src.models.institutional_holdings import Institute13F, InstitutionalHolding

def cleanup_institutions():
    """Clean up duplicate and test institutions."""
    # Initialize database connection
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get all institutions
        all_institutions = session.query(Institute13F).all()
        
        # Group institutions by name
        institutions_by_name = {}
        for inst in all_institutions:
            name = inst.institution_name
            if name not in institutions_by_name:
                institutions_by_name[name] = []
            institutions_by_name[name].append(inst)
        
        # Keep only the first institution for each name, delete others
        for name, institutions in institutions_by_name.items():
            if len(institutions) > 1:
                # Keep the first one
                keep_inst = institutions[0]
                print(f"Keeping {name} with ID {keep_inst.id}")
                
                # Delete the rest
                for inst in institutions[1:]:
                    print(f"Deleting duplicate {name} with ID {inst.id}")
                    
                    # Delete associated holdings
                    holdings_count = session.query(InstitutionalHolding).filter(
                        InstitutionalHolding.report_id == inst.id
                    ).delete()
                    print(f"Deleted {holdings_count} holdings for institution ID {inst.id}")
                    
                    # Delete the institution
                    session.delete(inst)
        
        # Delete test institution if it exists
        test_inst = session.query(Institute13F).filter(
            Institute13F.institution_name == "Test Institution"
        ).first()
        
        if test_inst:
            print(f"Deleting test institution with ID {test_inst.id}")
            
            # Delete associated holdings
            holdings_count = session.query(InstitutionalHolding).filter(
                InstitutionalHolding.report_id == test_inst.id
            ).delete()
            print(f"Deleted {holdings_count} holdings for test institution")
            
            # Delete the institution
            session.delete(test_inst)
        
        # Commit changes
        session.commit()
        print("Cleanup completed successfully.")
    
    except Exception as e:
        import traceback
        print(f"Error cleaning up institutions: {str(e)}")
        print("Full error:")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_institutions()
