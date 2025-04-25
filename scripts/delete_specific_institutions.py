import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.manager import DatabaseManager
from src.models.institutional_holdings import Institute13F, InstitutionalHolding

def delete_specific_institutions(ids_to_delete):
    """Delete specific institutions by ID."""
    # Initialize database connection
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        for inst_id in ids_to_delete:
            # Get the institution
            institution = session.query(Institute13F).filter(Institute13F.id == inst_id).first()
            
            if institution:
                print(f"Deleting institution {institution.institution_name} with ID {inst_id}")
                
                # Delete associated holdings
                holdings_count = session.query(InstitutionalHolding).filter(
                    InstitutionalHolding.report_id == inst_id
                ).delete()
                print(f"Deleted {holdings_count} holdings for institution ID {inst_id}")
                
                # Delete the institution
                session.delete(institution)
            else:
                print(f"Institution with ID {inst_id} not found")
        
        # Commit changes
        session.commit()
        print("Deletion completed successfully.")
    
    except Exception as e:
        import traceback
        print(f"Error deleting institutions: {str(e)}")
        print("Full error:")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # IDs to delete
    ids_to_delete = [8, 9]
    delete_specific_institutions(ids_to_delete)
